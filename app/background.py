"""Détourage (rembg / ONNX) et remplacement d'arrière-plan."""
import threading
from collections import OrderedDict

import cv2
import numpy as np
from PIL import Image

from . import config

_sessions: "OrderedDict[str, object]" = OrderedDict()
_lock = threading.Lock()


def get_session(name: str):
    """Charge un modèle de détourage à la demande ; garde les N derniers en mémoire."""
    import onnxruntime as ort
    from rembg import new_session

    with _lock:
        if name in _sessions:
            _sessions.move_to_end(name)
            return _sessions[name]
        # Sans arène ni plan mémoire, ONNX Runtime rend la mémoire après chaque
        # inférence au lieu de la garder réservée : indispensable sur un hôte mutualisé.
        opts = ort.SessionOptions()
        opts.enable_cpu_mem_arena = False
        opts.enable_mem_pattern = False
        opts.intra_op_num_threads = config.THREADS
        opts.inter_op_num_threads = 1
        session = new_session(name, sess_opts=opts)
        _sessions[name] = session
        while len(_sessions) > config.MAX_BG_SESSIONS:
            _sessions.popitem(last=False)
        return session


def loaded_models() -> list[str]:
    return list(_sessions.keys())


def predict_mask(rgb: np.ndarray, model: str) -> np.ndarray:
    """Masque de premier plan, float32 dans [0,1], à la taille de l'image."""
    session = get_session(model)
    mask = session.predict(Image.fromarray(rgb))[0]
    m = np.asarray(mask.convert("L"), dtype=np.float32) / 255.0
    if m.shape != rgb.shape[:2]:
        m = cv2.resize(m, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_LINEAR)
    return m


def _box(x: np.ndarray, r: int) -> np.ndarray:
    return cv2.boxFilter(x, cv2.CV_32F, (2 * r + 1, 2 * r + 1), borderType=cv2.BORDER_REFLECT)


def guided_filter(guide: np.ndarray, src: np.ndarray, r: int, eps: float) -> np.ndarray:
    """Filtre guidé (He et al.) avec un guide en niveaux de gris."""
    mean_i = _box(guide, r)
    mean_p = _box(src, r)
    cov_ip = _box(guide * src, r) - mean_i * mean_p
    var_i = _box(guide * guide, r) - mean_i * mean_i
    a = cov_ip / (var_i + eps)
    b = mean_p - a * mean_i
    return _box(a, r) * guide + _box(b, r)


def refine_edges(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Affine le masque dans la seule bande de transition, guidé par l'image.

    L'intérieur et l'extérieur sûrs gardent la décision du modèle : le filtre
    guidé n'agit que là où le modèle hésite (cheveux, fourrure, flou de bougé).
    """
    h, w = mask.shape
    r = max(2, round(max(h, w) / 400))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    refined = np.clip(guided_filter(gray, mask, r, 1e-4), 0, 1)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    sure_fg = cv2.erode((mask > 0.95).astype(np.uint8), k)
    sure_bg = cv2.erode((mask < 0.05).astype(np.uint8), k)
    band = (sure_fg == 0) & (sure_bg == 0)
    out = mask.copy()
    out[band] = refined[band]
    return out


def matting(rgb: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Matting fermé (pymatting via rembg) : alpha et couleurs de premier plan."""
    from rembg.bg import alpha_matting_cutout

    img = Image.fromarray(rgb)
    m = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
    erode = max(5, round(max(rgb.shape[:2]) / 150))
    cut = np.asarray(alpha_matting_cutout(img, m, 240, 10, erode))
    fg = cut[:, :, :3].astype(np.float32) / 255.0
    alpha = cut[:, :, 3].astype(np.float32) / 255.0
    return fg, alpha


def _smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _normalized_blur(img: np.ndarray, weight: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    num = cv2.GaussianBlur(img * weight[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(weight, (0, 0), sigma)
    return num, den


def decontaminate(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Retire le liseré de l'ancien fond sur les bords semi-transparents.

    Les couleurs des pixels de bord sont remplacées par un prolongement des
    couleurs sûres du sujet (convolution normalisée), à proportion de leur
    transparence.
    """
    img = rgb.astype(np.float32) / 255.0
    h, w = alpha.shape
    sigma = max(2.0, max(h, w) / 400.0)
    weight = (alpha > 0.95).astype(np.float32)
    num, den = _normalized_blur(img, weight, sigma)
    ext = num / np.maximum(den, 1e-6)[..., None]
    holes = den < 1e-3
    if holes.any():  # bords très larges : seconde passe plus étendue
        num2, den2 = _normalized_blur(img, weight, sigma * 6)
        ext2 = num2 / np.maximum(den2, 1e-6)[..., None]
        ext[holes] = ext2[holes]
        still = den2 < 1e-4
        ext[holes & still] = img[holes & still]
    t = _smoothstep(0.5, 0.97, alpha)[..., None]
    return img * t + ext * (1 - t)


def parse_color(value: str) -> tuple[float, float, float]:
    v = (value or "").strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6 or any(c not in "0123456789abcdefABCDEF" for c in v):
        raise ValueError(value)
    return tuple(int(v[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def compose(fg: np.ndarray, alpha: np.ndarray, background: np.ndarray) -> np.ndarray:
    a = alpha[..., None]
    return np.clip(fg * a + background * (1 - a), 0, 1)


def blurred_background(original: np.ndarray, alpha: np.ndarray, strength: float) -> np.ndarray:
    """Flou d'arrière-plan type « mode portrait », sans bavure du sujet dans le flou."""
    img = original.astype(np.float32) / 255.0
    h, w = alpha.shape
    sigma = (4.0 + 40.0 * strength) * max(1.0, max(h, w) / 1500.0)
    weight = np.clip(1.0 - alpha, 0, 1) ** 2
    num, den = _normalized_blur(img, weight, sigma)
    plain = cv2.GaussianBlur(img, (0, 0), sigma)
    bg = num / np.maximum(den, 1e-6)[..., None]
    low = (den < 0.02)[..., None]
    return np.where(low, plain, bg)


def cover(bg_rgb: np.ndarray, width: int, height: int) -> np.ndarray:
    """Redimensionne et recadre au centre pour couvrir width x height."""
    bh, bw = bg_rgb.shape[:2]
    k = max(width / bw, height / bh)
    nw, nh = max(width, round(bw * k)), max(height, round(bh * k))
    interp = cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC
    resized = cv2.resize(bg_rgb, (nw, nh), interpolation=interp)
    x0, y0 = (nw - width) // 2, (nh - height) // 2
    return resized[y0 : y0 + height, x0 : x0 + width].astype(np.float32) / 255.0

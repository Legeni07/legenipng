"""Correction d'image : analyse automatique puis réglages dosés de 0 à 100.

Ordre d'application : débruitage, balance des blancs, niveaux, exposition,
contraste local, netteté (sur la luminance), puis vibrance.
"""
import math

import cv2
import numpy as np

PARAMS = ("wb", "levels", "exposure", "local_contrast", "denoise", "sharpen", "vibrance")


def _gray_small(rgb: np.ndarray, side: int = 1024) -> np.ndarray:
    h, w = rgb.shape[:2]
    k = min(1.0, side / max(h, w))
    small = cv2.resize(rgb, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_AREA) if k < 1 else rgb
    return cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)


def estimate_noise(rgb: np.ndarray) -> float:
    """Écart-type du bruit (échelle 0-255), méthode d'Immerkær sur la pleine résolution."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    if h < 3 or w < 3:
        return 0.0
    kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    conv = cv2.filter2D(gray, cv2.CV_32F, kernel, borderType=cv2.BORDER_REFLECT)[1:-1, 1:-1]
    return float(math.sqrt(math.pi / 2.0) * np.abs(conv).sum() / (6.0 * (w - 2) * (h - 2)))


def analyze(rgb: np.ndarray) -> dict:
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    chroma = np.hypot(a, b)
    # Dominante mesurée sur les pixels presque neutres et ni bouchés ni brûlés :
    # une photo de pelouse n'a pas une « dominante verte » à corriger.
    neutral = (chroma < 20) & (L > 12) & (L < 95)
    if neutral.mean() > 0.05:
        cast_a, cast_b = float(a[neutral].mean()), float(b[neutral].mean())
        cast_source = "neutral"
    else:
        cast_a, cast_b = float(a.mean()) * 0.5, float(b.mean()) * 0.5
        cast_source = "global"
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return {
        "mean_l": round(float(L.mean()), 1),
        "std_l": round(float(L.std()), 1),
        "p1": round(float(np.percentile(L, 1)), 1),
        "p99": round(float(np.percentile(L, 99)), 1),
        "cast_a": round(cast_a, 2),
        "cast_b": round(cast_b, 2),
        "cast_source": cast_source,
        "noise": round(estimate_noise(rgb), 2),
        "sharpness": round(float(cv2.Laplacian(_gray_small(rgb), cv2.CV_32F).var()), 1),
        "saturation": round(float(hsv[..., 1].mean()) / 255.0, 3),
    }


def auto_params(an: dict) -> dict:
    """Déduit des dosages raisonnables de l'analyse."""
    cast = math.hypot(an["cast_a"], an["cast_b"])
    p = {
        "wb": int(np.clip((cast - 2.0) * 12.0, 0, 85)),
        "levels": 70 if (an["p1"] > 3 or an["p99"] < 96) else 40,
        "exposure": 0,
        "local_contrast": 45 if an["std_l"] < 15 else 25,
        "denoise": int(np.clip((an["noise"] - 2.0) * 12.0, 0, 80)),
        "sharpen": 55 if an["sharpness"] < 60 else (35 if an["sharpness"] < 250 else 15),
        "vibrance": 35 if an["saturation"] < 0.22 else (20 if an["saturation"] < 0.40 else 0),
    }
    if abs(an["mean_l"] - 50.0) > 12.0:
        p["exposure"] = 60
    if p["denoise"] >= 40:  # ne pas réaccentuer le bruit qu'on vient d'enlever
        p["sharpen"] = min(p["sharpen"], 25)
    return p


def _smooth_strength(v) -> float:
    return float(np.clip(v, 0, 100)) / 100.0


def apply(rgb: np.ndarray, params: dict) -> np.ndarray:
    """Applique les corrections ; params : dict de PARAMS -> 0..100."""
    k = {name: _smooth_strength(params.get(name, 0)) for name in PARAMS}
    h, w = rgb.shape[:2]
    scale = max(h, w) / 1500.0

    out = rgb
    if k["denoise"] > 0:
        hval = 2.0 + 10.0 * k["denoise"]
        bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
        bgr = cv2.fastNlMeansDenoisingColored(bgr, None, hval, hval, 7, 15)
        out = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    lab = cv2.cvtColor(out.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    L, a, b = cv2.split(lab)

    if k["wb"] > 0:
        an = analyze(out)
        # Les blancs écrêtés sont neutres par construction : les décaler les teinterait
        t = np.clip((L - 90.0) / 9.5, 0, 1)
        protect = 1.0 - t * t * (3 - 2 * t)
        weight = np.clip(L / 100.0, 0, 1) * 1.1 * k["wb"] * protect
        a = a - an["cast_a"] * weight
        b = b - an["cast_b"] * weight

    if k["levels"] > 0:
        lo, hi = (float(v) for v in np.percentile(L, (0.5, 99.5)))
        if hi - lo > 10:
            stretched = (L - lo) * (100.0 / (hi - lo))
            L = L + (stretched - L) * k["levels"]

    if k["exposure"] > 0:
        m = float(np.clip(np.median(L) / 100.0, 0.05, 0.95))
        gamma = float(np.clip(math.log(0.48) / math.log(m), 0.55, 1.8))
        adjusted = 100.0 * np.power(np.clip(L / 100.0, 0, 1), gamma)
        L = L + (adjusted - L) * k["exposure"]

    if k["local_contrast"] > 0:
        L16 = np.clip(L / 100.0 * 65535.0, 0, 65535).astype(np.uint16)
        tiles = 8 if max(h, w) < 2500 else 12
        clahe = cv2.createCLAHE(clipLimit=1.5 + 2.0 * k["local_contrast"], tileGridSize=(tiles, tiles))
        eq = clahe.apply(L16).astype(np.float32) / 65535.0 * 100.0
        L = L + (eq - L) * min(1.0, k["local_contrast"] * 1.5)

    if k["sharpen"] > 0:
        sigma = (1.0 + 0.6 * k["sharpen"]) * max(1.0, scale)
        blur = cv2.GaussianBlur(L, (0, 0), sigma)
        detail = L - blur
        # seuil doux : on n'accentue pas le grain des aplats
        detail = np.where(np.abs(detail) < 0.6, detail * 0.3, detail)
        L = L + detail * (0.3 + 1.2 * k["sharpen"])

    L = np.clip(L, 0, 100)
    # NumPy 2 promeut en float64 au moindre scalaire numpy : on resserre avant OpenCV
    lab = cv2.merge([np.asarray(c, np.float32) for c in (L, a, b)])
    rgbf = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), 0, 1)

    if k["vibrance"] > 0:
        hsv = cv2.cvtColor(rgbf, cv2.COLOR_RGB2HSV)
        s = hsv[..., 1]
        hsv[..., 1] = np.clip(s * (1.0 + 0.8 * k["vibrance"] * (1.0 - s)), 0, 1)
        rgbf = np.clip(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), 0, 1)

    return (rgbf * 255.0 + 0.5).astype(np.uint8)

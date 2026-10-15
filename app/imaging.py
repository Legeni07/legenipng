"""Décodage sûr des images reçues et encodage des résultats."""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

from . import config

try:  # photos HEIC/HEIF des iPhone
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF = True
except Exception:  # pragma: no cover - dépendance facultative
    HEIF = False

Image.MAX_IMAGE_PIXELS = config.MAX_DECODE_PIXELS

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "MPO", "HEIF", "AVIF"}


class InputError(Exception):
    """Erreur imputable au fichier envoyé : renvoyée telle quelle au client."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def load_image(data: bytes) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """Renvoie (rgb uint8 HxWx3, alpha uint8 HxW ou None, infos).

    Le format est établi en décodant le contenu, jamais d'après l'extension.
    L'orientation EXIF est appliquée puis toutes les métadonnées sont abandonnées.
    """
    if not data:
        raise InputError("empty", "Fichier vide.")
    try:
        im = Image.open(io.BytesIO(data))
        fmt = im.format
        if fmt not in ALLOWED_FORMATS:
            raise InputError("unsupported_format", f"Format non pris en charge : {fmt or 'inconnu'}.", 415)
        if getattr(im, "n_frames", 1) > 1:
            im.seek(0)
        im.load()
    except InputError:
        raise
    except Image.DecompressionBombError:
        raise InputError("too_many_pixels", "Image trop grande (nombre de pixels).", 413)
    except Exception:
        raise InputError("bad_image", "Fichier illisible : ce n'est pas une image valide.", 415)

    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass  # EXIF corrompu : on garde l'orientation brute

    if im.mode in ("I;16", "I;16B", "I;16L", "I", "F"):
        arr = np.asarray(im).astype(np.float32)
        peak = float(arr.max()) or 1.0
        im = Image.fromarray(np.clip(arr / peak * 255.0, 0, 255).astype(np.uint8), "L")

    has_alpha = im.mode in ("RGBA", "LA", "PA", "RGBa", "La") or (
        im.mode == "P" and "transparency" in im.info
    )
    im = im.convert("RGBA" if has_alpha else "RGB")
    arr = np.array(im)  # copie modifiable
    info = {"format": fmt, "width": arr.shape[1], "height": arr.shape[0], "alpha": has_alpha}
    if has_alpha:
        alpha = arr[:, :, 3].copy()
        if alpha.min() == 255:  # canal alpha présent mais entièrement opaque
            alpha = None
        return np.ascontiguousarray(arr[:, :, :3]), alpha, info
    return arr, None, info


def fit_within(rgb: np.ndarray, alpha: np.ndarray | None, max_side: int):
    """Réduit l'image si son plus grand côté dépasse max_side. Renvoie (rgb, alpha, réduit?)."""
    h, w = rgb.shape[:2]
    side = max(h, w)
    if side <= max_side:
        return rgb, alpha, False
    k = max_side / side
    size = (max(1, round(w * k)), max(1, round(h * k)))
    rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
    if alpha is not None:
        alpha = cv2.resize(alpha, size, interpolation=cv2.INTER_AREA)
    return rgb, alpha, True


MIME = {"png": "image/png", "webp": "image/webp", "jpg": "image/jpeg"}


def encode_image(rgb: np.ndarray, alpha: np.ndarray | None, fmt: str) -> bytes:
    """Encode sans aucune métadonnée (ni EXIF, ni GPS, ni profil)."""
    if fmt == "jpg" and alpha is not None:
        a = alpha.astype(np.float32)[..., None] / 255.0
        rgb = np.clip(rgb.astype(np.float32) * a + 255.0 * (1.0 - a) + 0.5, 0, 255).astype(np.uint8)
        alpha = None
    if alpha is not None:
        im = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    else:
        im = Image.fromarray(rgb, "RGB")
    buf = io.BytesIO()
    if fmt == "png":
        im.save(buf, "PNG", optimize=False, compress_level=6)
    elif fmt == "webp":
        im.save(buf, "WEBP", quality=92, method=4)
    else:
        im.save(buf, "JPEG", quality=92, subsampling=0, optimize=True)
    return buf.getvalue()

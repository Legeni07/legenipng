"""Agrandissement par IA : Real-ESRGAN (réseau génératif antagoniste) exporté en ONNX.

Le modèle est appliqué par tuiles avec recouvrement, ce qui borne la mémoire
quelle que soit la taille de l'image.
"""
import os
import threading

import cv2
import numpy as np
import onnxruntime as ort

from . import config

# Pas de télémétrie Microsoft depuis la plateforme (vaut aussi pour les sessions rembg)
ort.disable_telemetry_events()

_sessions: dict[str, ort.InferenceSession] = {}
_lock = threading.Lock()
SCALE = 4
PAD = 16


def available_levels() -> list[str]:
    return [lvl for lvl, f in config.SR_LEVELS.items() if os.path.exists(os.path.join(config.SR_DIR, f))]


def get_session(level: str) -> ort.InferenceSession:
    with _lock:
        if level not in _sessions:
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = config.THREADS
            opts.inter_op_num_threads = 1
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            path = os.path.join(config.SR_DIR, config.SR_LEVELS[level])
            _sessions[level] = ort.InferenceSession(path, opts, providers=["CPUExecutionProvider"])
        return _sessions[level]


def _run_x4(img: np.ndarray, level: str) -> np.ndarray:
    """img : float32 HxWx3 dans [0,1] -> float32 (4H)x(4W)x3."""
    session = get_session(level)
    name = session.get_inputs()[0].name
    chw = np.ascontiguousarray(img.transpose(2, 0, 1))
    _, h, w = chw.shape
    out = np.empty((3, h * SCALE, w * SCALE), np.float32)
    tile = config.SR_TILE
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
            py0, px0 = max(y0 - PAD, 0), max(x0 - PAD, 0)
            py1, px1 = min(y1 + PAD, h), min(x1 + PAD, w)
            patch = chw[None, :, py0:py1, px0:px1]
            res = session.run(None, {name: patch})[0][0]
            oy, ox = (y0 - py0) * SCALE, (x0 - px0) * SCALE
            out[:, y0 * SCALE : y1 * SCALE, x0 * SCALE : x1 * SCALE] = res[
                :, oy : oy + (y1 - y0) * SCALE, ox : ox + (x1 - x0) * SCALE
            ]
    return np.clip(out.transpose(1, 2, 0), 0, 1)


def upscale(rgb: np.ndarray, alpha: np.ndarray | None, factor: int, level: str):
    """Agrandit rgb (uint8) d'un facteur 2 ou 4 ; l'alpha suit par interpolation."""
    h, w = rgb.shape[:2]
    big = _run_x4(rgb.astype(np.float32) / 255.0, level)
    size = (w * factor, h * factor)
    if factor != SCALE:
        big = cv2.resize(big, size, interpolation=cv2.INTER_AREA)
    out = (big * 255.0 + 0.5).astype(np.uint8)
    if alpha is not None:
        alpha = cv2.resize(alpha, size, interpolation=cv2.INTER_CUBIC)
    return out, alpha


def self_test() -> bool:
    """Vérifie au démarrage que le modèle se charge et produit la bonne taille."""
    levels = available_levels()
    if not levels:
        return False
    probe = np.random.default_rng(0).random((24, 40, 3), dtype=np.float32)
    res = _run_x4(probe, "medium" if "medium" in levels else levels[0])
    return res.shape == (96, 160, 3) and bool(np.isfinite(res).all())

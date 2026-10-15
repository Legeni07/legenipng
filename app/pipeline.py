"""Enchaînement des traitements : correction -> détourage -> fond -> agrandissement."""
import time
from dataclasses import dataclass, field

import numpy as np

from . import background, config, enhance, imaging, superres


@dataclass
class Options:
    enhance: str = "off"  # off | auto | manual
    manual: dict = field(default_factory=dict)
    remove_bg: bool = False
    model: str = config.DEFAULT_BG_MODEL
    edges: str = "refined"  # standard | refined | matting
    bg_mode: str = "transparent"  # transparent | color | blur | image
    bg_color: tuple = (1.0, 1.0, 1.0)
    bg_blur: int = 50
    upscale: int = 1  # 1 | 2 | 4
    sr_denoise: str = "medium"  # low | medium | high
    fmt: str = "png"  # png | webp | jpg


class _Clock:
    def __init__(self):
        self.steps = []

    def step(self, name: str, t0: float, **details):
        self.steps.append({"step": name, "ms": round((time.perf_counter() - t0) * 1000), **details})


def run(data: bytes, bg_data: bytes | None, opt: Options) -> tuple[bytes, dict]:
    clock = _Clock()
    notes = []

    t = time.perf_counter()
    rgb, alpha, info = imaging.load_image(data)
    clock.step("decode", t, format=info["format"])

    bg_rgb = None
    if opt.remove_bg and opt.bg_mode == "image":
        if not bg_data:
            raise imaging.InputError("missing_background", "Image d'arrière-plan manquante.")
        bg_rgb, _, _ = imaging.load_image(bg_data)

    limit = config.MAX_SIDE
    if opt.remove_bg and opt.edges == "matting":
        limit = min(limit, config.MATTING_MAX_SIDE)
    if opt.upscale > 1:
        limit = min(limit, config.SR_MAX_SIDE[opt.upscale])
    rgb, alpha, reduced = imaging.fit_within(rgb, alpha, limit)
    if reduced:
        notes.append({"code": "reduced", "side": limit, "width": rgb.shape[1], "height": rgb.shape[0]})

    if opt.enhance != "off":
        t = time.perf_counter()
        analysis = enhance.analyze(rgb)
        params = enhance.auto_params(analysis) if opt.enhance == "auto" else dict(opt.manual)
        rgb = enhance.apply(rgb, params)
        clock.step("enhance", t, mode=opt.enhance, params=params, analysis=analysis)

    fg = None  # couleurs de premier plan en float [0,1]
    if opt.remove_bg:
        t = time.perf_counter()
        mask = background.predict_mask(rgb, opt.model)
        clock.step("segment", t, model=opt.model)
        t = time.perf_counter()
        if opt.edges == "matting":
            fg, new_alpha = background.matting(rgb, mask)
        else:
            new_alpha = background.refine_edges(rgb, mask) if opt.edges == "refined" else mask
            fg = background.decontaminate(rgb, new_alpha)
        if alpha is not None:  # l'image avait déjà de la transparence : on la conserve
            new_alpha = new_alpha * (alpha.astype(np.float32) / 255.0)
        coverage = float(new_alpha.mean())
        if coverage < 0.005:
            notes.append({"code": "empty_mask"})
        clock.step("edges", t, mode=opt.edges, coverage=round(coverage, 3))

        if opt.bg_mode != "transparent":
            t = time.perf_counter()
            h, w = new_alpha.shape
            if opt.bg_mode == "color":
                backdrop = np.empty((h, w, 3), np.float32)
                backdrop[:] = opt.bg_color
            elif opt.bg_mode == "blur":
                backdrop = background.blurred_background(rgb, new_alpha, opt.bg_blur / 100.0)
            else:
                backdrop = background.cover(bg_rgb, w, h)
            fg = background.compose(fg, new_alpha, backdrop)
            alpha = None
            clock.step("background", t, mode=opt.bg_mode)
        else:
            alpha = (np.clip(new_alpha, 0, 1) * 255.0 + 0.5).astype(np.uint8)
        rgb = (np.clip(fg, 0, 1) * 255.0 + 0.5).astype(np.uint8)

    if opt.upscale > 1:
        t = time.perf_counter()
        rgb, alpha = superres.upscale(rgb, alpha, opt.upscale, opt.sr_denoise)
        clock.step("upscale", t, factor=opt.upscale, denoise=opt.sr_denoise)

    t = time.perf_counter()
    fmt = opt.fmt
    out = imaging.encode_image(rgb, alpha, fmt)
    clock.step("encode", t, format=fmt)
    if fmt == "jpg" and opt.remove_bg and opt.bg_mode == "transparent":
        notes.append({"code": "jpg_flattened"})

    report = {
        "version": config.VERSION,
        "input": {k: info[k] for k in ("format", "width", "height")},
        "output": {"format": fmt, "width": rgb.shape[1], "height": rgb.shape[0], "bytes": len(out),
                   "transparent": alpha is not None and fmt != "jpg"},
        "steps": clock.steps,
        "notes": notes,
        "total_ms": sum(s["ms"] for s in clock.steps),
    }
    return out, report

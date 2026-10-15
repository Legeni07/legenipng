"""LegeniPNG — API et interface de la plateforme de test de traitement d'image."""
import asyncio
import json
import logging
import os
import threading
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from . import background, config, enhance, imaging, pipeline, superres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("legenipng")
cv2.setNumThreads(config.THREADS)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_warm_up, name="warm-up", daemon=True).start()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LegeniPNG",
    version=config.VERSION,
    description="Plateforme de test : détourage, correction et agrandissement d'images par IA (CPU).",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

STATE = {"sr_ok": None, "warm": False}

CSP = (
    "default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; "
    "form-action 'self'; frame-ancestors 'none'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # Swagger charge ses scripts depuis un CDN : la page de doc est exemptée de la CSP
    if not request.url.path.startswith("/api/docs"):
        response.headers["Content-Security-Policy"] = CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path in ("/", "/index.html") or request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


class Busy(Exception):
    pass


class JobGate:
    """Sérialise les calculs lourds et refuse au-delà d'une file d'attente bornée."""

    def __init__(self, slots: int, queue_max: int):
        self.sem = asyncio.Semaphore(slots)
        self.limit = slots + queue_max
        self.pending = 0

    async def run(self, fn, *args):
        if self.pending >= self.limit:
            raise Busy()
        self.pending += 1
        try:
            async with self.sem:
                return await run_in_threadpool(fn, *args)
        finally:
            self.pending -= 1


gate = JobGate(config.MAX_JOBS, config.QUEUE_MAX)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"code": code, "detail": message}, status_code=status)


def _warm_up():
    """Charge le modèle par défaut et compile le matting hors du chemin des requêtes."""
    try:
        STATE["sr_ok"] = superres.self_test()
        log.info("agrandissement IA : %s", "ok" if STATE["sr_ok"] else "INDISPONIBLE")
    except Exception:
        STATE["sr_ok"] = False
        log.exception("échec de l'auto-test de l'agrandissement")
    try:
        background.get_session(config.DEFAULT_BG_MODEL)
        probe = np.full((48, 48, 3), 128, np.uint8)
        mask = np.zeros((48, 48), np.float32)
        mask[12:36, 12:36] = 1.0
        background.matting(probe, mask)  # compilation numba de pymatting
        STATE["warm"] = True
        log.info("modèles préchargés : %s", background.loaded_models())
    except Exception:
        log.exception("échec du préchargement")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": config.VERSION,
        "warm": STATE["warm"],
        "upscale_ready": bool(STATE["sr_ok"]),
        "loaded_models": background.loaded_models(),
        "pending_jobs": gate.pending,
    }


@app.get("/api/config")
async def get_config():
    return {
        "version": config.VERSION,
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "max_side": config.MAX_SIDE,
        "matting_max_side": config.MATTING_MAX_SIDE,
        "upscale_max_side": {str(k): v for k, v in config.SR_MAX_SIDE.items()},
        "upscale_levels": superres.available_levels(),
        "models": config.BG_MODELS,
        "default_model": config.DEFAULT_BG_MODEL,
        "heif": imaging.HEIF,
        "enhance_params": list(enhance.PARAMS),
    }


def _choice(value: str, allowed, name: str) -> str:
    if value not in allowed:
        raise imaging.InputError("bad_option", f"Valeur invalide pour « {name} » : {value!r}.")
    return value


def _strength(value: str, name: str) -> int:
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        raise imaging.InputError("bad_option", f"Valeur invalide pour « {name} ».")
    if not 0 <= v <= 100:
        raise imaging.InputError("bad_option", f"« {name} » doit être compris entre 0 et 100.")
    return v


async def _read_limited(upload: UploadFile) -> bytes:
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise imaging.InputError("too_large", f"Fichier trop lourd (maximum {config.MAX_UPLOAD_MB} Mo).", 413)
    return data


@app.post("/api/process")
async def process(
    image: UploadFile = File(..., description="Image source (JPEG, PNG, WebP, HEIC…)"),
    background_image: UploadFile | None = File(None, description="Nouveau fond si bg_mode=image"),
    enhance_mode: str = Form("off", description="off | auto | manual"),
    wb: str = Form("0"),
    levels: str = Form("0"),
    exposure: str = Form("0"),
    local_contrast: str = Form("0"),
    denoise: str = Form("0"),
    sharpen: str = Form("0"),
    vibrance: str = Form("0"),
    remove_bg: bool = Form(False),
    model: str = Form(config.DEFAULT_BG_MODEL),
    edges: str = Form("refined", description="standard | refined | matting"),
    bg_mode: str = Form("transparent", description="transparent | color | blur | image"),
    bg_color: str = Form("#ffffff"),
    bg_blur: str = Form("50"),
    upscale: str = Form("1", description="1 | 2 | 4"),
    sr_denoise: str = Form("medium", description="low | medium | high"),
    output_format: str = Form("png", description="png | webp | jpg"),
):
    try:
        opt = pipeline.Options(
            enhance=_choice(enhance_mode, ("off", "auto", "manual"), "enhance_mode"),
            remove_bg=remove_bg,
            model=_choice(model, config.BG_MODEL_IDS, "model"),
            edges=_choice(edges, ("standard", "refined", "matting"), "edges"),
            bg_mode=_choice(bg_mode, ("transparent", "color", "blur", "image"), "bg_mode"),
            bg_blur=_strength(bg_blur, "bg_blur"),
            upscale=int(_choice(upscale, ("1", "2", "4"), "upscale")),
            sr_denoise=_choice(sr_denoise, tuple(config.SR_LEVELS), "sr_denoise"),
            fmt=_choice(output_format, tuple(imaging.MIME), "output_format"),
        )
        if opt.enhance == "manual":
            values = dict(wb=wb, levels=levels, exposure=exposure, local_contrast=local_contrast,
                          denoise=denoise, sharpen=sharpen, vibrance=vibrance)
            opt.manual = {k: _strength(v, k) for k, v in values.items()}
        try:
            opt.bg_color = background.parse_color(bg_color)
        except ValueError:
            raise imaging.InputError("bad_option", "Couleur de fond invalide (format #rrggbb attendu).")
        if opt.upscale > 1 and opt.sr_denoise not in superres.available_levels():
            return _error(503, "upscale_unavailable", "Agrandissement IA indisponible sur ce serveur.")

        data = await _read_limited(image)
        bg_data = None
        if opt.remove_bg and opt.bg_mode == "image" and background_image is not None:
            bg_data = await _read_limited(background_image)

        out, report = await gate.run(pipeline.run, data, bg_data, opt)
    except imaging.InputError as e:
        return _error(e.status, e.code, e.message)
    except Busy:
        return _error(503, "busy", "La plateforme est occupée, réessayez dans quelques instants.")
    except Exception:
        log.exception("échec du traitement")
        return _error(500, "internal", "Le traitement a échoué de façon inattendue.")

    log.info(
        "traitement %sx%s -> %sx%s en %d ms (%s)",
        report["input"]["width"], report["input"]["height"],
        report["output"]["width"], report["output"]["height"],
        report["total_ms"], ",".join(s["step"] for s in report["steps"]),
    )
    return Response(
        content=out,
        media_type=imaging.MIME[opt.fmt],
        headers={
            "X-Legenipng-Report": json.dumps(report, ensure_ascii=True, separators=(",", ":")),
            "Content-Disposition": f'inline; filename="legenipng.{opt.fmt}"',
        },
    )


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

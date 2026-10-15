# syntax=docker/dockerfile:1

# --- Étape jetable : export de Real-ESRGAN en ONNX (PyTorch ne va pas dans l'image finale)
FROM python:3.12-slim-bookworm AS sr-export
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install onnx==1.17.0 "numpy<2.2"
WORKDIR /export
ADD https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth ./
ADD https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth ./
COPY tools/export_realesrgan.py ./
RUN sha256sum *.pth && python export_realesrgan.py \
      --strong realesr-general-x4v3.pth --weak realesr-general-wdn-x4v3.pth --out /export/onnx

# --- Image d'exécution
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    U2NET_HOME=/models/rembg \
    LEGENIPNG_SR_DIR=/models/sr \
    NUMBA_CACHE_DIR=/tmp/numba \
    MPLCONFIGDIR=/tmp/mpl \
    OMP_NUM_THREADS=4 \
    ORT_DISABLE_TELEMETRY=1 \
    HOME=/home/app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
# requirements.lock : versions exactes validées en production (voir README, « Mettre à jour les dépendances »)
COPY requirements.txt requirements.lock ./
RUN pip install -r requirements.lock \
 && pip check \
 && python -c "import cv2, onnxruntime, rembg, pillow_heif; print('cv2', cv2.__version__, '| ort', onnxruntime.__version__)"

COPY tools/fetch_models.py /tmp/fetch_models.py
RUN python /tmp/fetch_models.py isnet-general-use u2net u2net_human_seg u2netp \
 && rm /tmp/fetch_models.py && du -sh /models/rembg

COPY --from=sr-export /export/onnx/ /models/sr/

# Cache numba pré-compilé (matting) : recopié dans /tmp au démarrage
COPY app/config.py app/background.py /srv/app/
COPY tools/warm_numba.py /tmp/warm_numba.py
RUN NUMBA_CACHE_DIR=/opt/numba-seed PYTHONPATH=/srv python /tmp/warm_numba.py \
 && rm /tmp/warm_numba.py && rm -rf /srv/app/__pycache__

COPY app/ /srv/app/

RUN useradd -r -m -d /home/app -s /usr/sbin/nologin app \
 && chmod -R a=rX /srv /models /opt/numba-seed

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"
CMD ["sh", "-c", "mkdir -p /tmp/numba && cp -r /opt/numba-seed/. /tmp/numba/ && chmod -R u+w /tmp/numba && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips '*' --timeout-keep-alive 30 --no-server-header"]

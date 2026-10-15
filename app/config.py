"""Paramètres de LegeniPNG, tous surchargeables par variables d'environnement."""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


VERSION = "1.0.0"

# Limites d'entrée
MAX_UPLOAD_MB = _int("LEGENIPNG_MAX_UPLOAD_MB", 15)
MAX_DECODE_PIXELS = _int("LEGENIPNG_MAX_DECODE_PIXELS", 50_000_000)
# Côté le plus long au-delà duquel l'image est réduite avant traitement
MAX_SIDE = _int("LEGENIPNG_MAX_SIDE", 3000)
# Le matting (bords « haute précision ») est coûteux : on travaille plus petit
MATTING_MAX_SIDE = _int("LEGENIPNG_MATTING_MAX_SIDE", 2048)
# Taille d'entrée maximale de l'agrandissement IA, par facteur
SR_MAX_SIDE = {
    2: _int("LEGENIPNG_SR_MAX_SIDE_X2", 1200),
    4: _int("LEGENIPNG_SR_MAX_SIDE_X4", 720),
}
SR_TILE = _int("LEGENIPNG_SR_TILE", 256)

# Concurrence : un serveur sans GPU, mutualisé — on sérialise les calculs
MAX_JOBS = _int("LEGENIPNG_MAX_JOBS", 1)
QUEUE_MAX = _int("LEGENIPNG_QUEUE_MAX", 8)
THREADS = _int("LEGENIPNG_THREADS", 4)
# Nombre de modèles de détourage gardés en mémoire en même temps
MAX_BG_SESSIONS = _int("LEGENIPNG_MAX_BG_SESSIONS", 2)

SR_DIR = os.environ.get("LEGENIPNG_SR_DIR", "/models/sr")

# Modèles de détourage proposés (noms de session rembg)
BG_MODELS = [
    {
        "id": "isnet-general-use",
        "fr": "Polyvalent (ISNet)",
        "en": "General purpose (ISNet)",
        "hint_fr": "Bon compromis qualité / vitesse pour la plupart des photos.",
        "hint_en": "Good quality/speed balance for most photos.",
    },
    # BiRefNet a été écarté : entrée figée à 1024 px et plus de 5 Go de RAM sur CPU.
    {
        "id": "u2net",
        "fr": "Classique (U²-Net)",
        "en": "Classic (U²-Net)",
        "hint_fr": "Autre avis sur les images où ISNet hésite (objets, animaux).",
        "hint_en": "A second opinion where ISNet struggles (objects, animals).",
    },
    {
        "id": "u2net_human_seg",
        "fr": "Personnes (U²-Net humain)",
        "en": "People (U²-Net human)",
        "hint_fr": "Spécialisé portraits et silhouettes.",
        "hint_en": "Specialised for portraits and full-body shots.",
    },
    {
        "id": "u2netp",
        "fr": "Rapide (U²-Net léger)",
        "en": "Fast (lightweight U²-Net)",
        "hint_fr": "Très rapide, contours plus grossiers.",
        "hint_en": "Very fast, coarser edges.",
    },
]
BG_MODEL_IDS = [m["id"] for m in BG_MODELS]
DEFAULT_BG_MODEL = "isnet-general-use"

# Agrandissement IA : Real-ESRGAN general x4v3, interpolé à 3 niveaux de débruitage
SR_LEVELS = {
    "low": "realesr-general-x4v3_dn0.onnx",
    "medium": "realesr-general-x4v3_dn50.onnx",
    "high": "realesr-general-x4v3_dn100.onnx",
}

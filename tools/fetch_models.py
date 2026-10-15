"""Télécharge les modèles de détourage rembg dans $U2NET_HOME pendant la construction.

Ainsi le conteneur démarre sans accès réseau et en système de fichiers en lecture seule.
"""
import sys

from rembg.sessions import sessions_class

wanted = set(sys.argv[1:])
found = set()
for cls in sessions_class:
    if cls.name() in wanted:
        print(f"téléchargement : {cls.name()}", flush=True)
        cls.download_models()
        found.add(cls.name())

missing = wanted - found
if missing:
    sys.exit(f"modèles inconnus de cette version de rembg : {sorted(missing)}")

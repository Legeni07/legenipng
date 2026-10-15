"""Compile à la construction les fonctions numba de pymatting (matting des bords).

Le cache produit dans $NUMBA_CACHE_DIR est recopié dans /tmp au démarrage du
conteneur : sans lui, chaque redémarrage occupe 4 cœurs pendant ~2 minutes.
"""
import numpy as np

from app import background

probe = np.full((48, 48, 3), 128, np.uint8)
mask = np.zeros((48, 48), np.float32)
mask[12:36, 12:36] = 1.0
background.matting(probe, mask)
print("cache numba prêt")

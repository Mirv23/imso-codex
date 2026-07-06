"""Résolution du stockage des fichiers sensibles.

`private_media_storage` est une *callable* (et non une instance) pour deux
raisons : Django la déconstruit par son chemin d'import dans les migrations (le
chemin reste stable même si la config change), et l'instance concrète est
résolue à l'exécution — ce qui permet au repli disque de dev de fonctionner.
"""
from __future__ import annotations

from django.core.files.storage import storages


def private_media_storage():
    """Stockage des fichiers sensibles : URLs signées à durée limitée en prod,
    disque local en dev. Défini dans settings.STORAGES["private"]."""
    return storages["private"]

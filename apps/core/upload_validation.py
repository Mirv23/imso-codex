"""Validation robuste des fichiers image téléversés.

La validation historique se basait uniquement sur `file.content_type` — une
en-tête FOURNIE PAR LE CLIENT, donc falsifiable : un fichier arbitraire (SVG
contenant du <script>, HTML, polyglotte) pouvait passer en se déclarant
`image/png`. Certaines cibles vont dans un bucket PUBLIC (produits/blog/logo) ->
XSS stocké potentiel si le SVG est servi inline.

On valide donc ici SANS dépendance externe (pas de Pillow requis) :
  1. taille max,
  2. allowlist d'extensions,
  3. signature binaire (octets magiques) réellement lue dans le fichier.
Le SVG est refusé (pas de signature binaire fiable, vecteur XSS).
"""
from __future__ import annotations

import os

# Extensions autorisées (raster uniquement — pas de SVG).
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 Mo


def _has_image_signature(head: bytes) -> bool:
    """Vrai si `head` (>=12 premiers octets) commence par une signature d'image
    raster connue."""
    if head.startswith(b"\xff\xd8\xff"):            # JPEG
        return True
    if head.startswith(b"\x89PNG\r\n\x1a\n"):       # PNG
        return True
    if head[:6] in (b"GIF87a", b"GIF89a"):          # GIF
        return True
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":  # WEBP (conteneur RIFF)
        return True
    return False


def validate_image_upload(f, *, max_bytes: int = DEFAULT_MAX_BYTES) -> str | None:
    """Valide un fichier téléversé comme image. Renvoie un message d'erreur
    (str) si invalide, ou None si tout est bon. Ne consomme pas le pointeur de
    lecture (remis à 0)."""
    if f is None:
        return "Aucun fichier fourni."
    if getattr(f, "size", 0) > max_bytes:
        return f"Fichier trop volumineux (max {max_bytes // (1024 * 1024)} Mo)."
    ext = os.path.splitext(getattr(f, "name", "") or "")[1].lower().lstrip(".")
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return "Format non autorisé. Utilisez une image JPG, PNG, WEBP ou GIF."
    try:
        head = f.read(12)
        f.seek(0)
    except Exception:
        return "Fichier illisible."
    if not _has_image_signature(head):
        return "Le fichier n'est pas une image valide (contenu non reconnu)."
    return None

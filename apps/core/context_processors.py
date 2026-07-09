"""Injecte les paramètres du site dans tous les templates."""

from __future__ import annotations


def site_settings(request):
    """Expose `site` (SiteSetting) à tous les templates.

    Robuste : si la table n'existe pas encore (avant migration) ou en cas
    d'erreur DB, renvoie None au lieu de casser le rendu (ex. healthcheck).
    """
    try:
        from apps.adminpanel.models import SiteSetting, SiteText, SiteImage
        # `texts` : registre des textes editables (titres/intitules...) charge en
        # UNE requete et expose comme dict {cle: valeur} pour un fallback template
        # {{ texts.cle|default:"..." }}. Les valeurs vides sont ignorees (fallback).
        texts = {t.key: t.value for t in SiteText.objects.all() if t.value}
        # `images` : registre des images editables, expose comme dict {cle: objet}
        # (une requete) pour {% if images.cle %}<img src="{{ images.cle.image.url }}">.
        # Les entrees sans fichier sont ignorees -> le template garde son image
        # codee en dur. try/except separe : une table absente ne casse pas texts.
        try:
            images = {t.key: t for t in SiteImage.objects.all() if t.image}
        except Exception:
            images = {}
        return {"site": SiteSetting.load(), "texts": texts, "images": images}
    except Exception:
        return {"site": None, "texts": {}, "images": {}}

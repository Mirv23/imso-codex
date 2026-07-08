"""Injecte les paramètres du site dans tous les templates."""

from __future__ import annotations


def site_settings(request):
    """Expose `site` (SiteSetting) à tous les templates.

    Robuste : si la table n'existe pas encore (avant migration) ou en cas
    d'erreur DB, renvoie None au lieu de casser le rendu (ex. healthcheck).
    """
    try:
        from apps.adminpanel.models import SiteSetting, SiteText
        # `texts` : registre des textes editables (titres/intitules...) charge en
        # UNE requete et expose comme dict {cle: valeur} pour un fallback template
        # {{ texts.cle|default:"..." }}. Les valeurs vides sont ignorees (fallback).
        texts = {t.key: t.value for t in SiteText.objects.all() if t.value}
        return {"site": SiteSetting.load(), "texts": texts}
    except Exception:
        return {"site": None, "texts": {}}

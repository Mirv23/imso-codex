"""Injecte les paramètres du site dans tous les templates."""

from __future__ import annotations


def site_settings(request):
    """Expose `site` (SiteSetting) à tous les templates.

    Robuste : si la table n'existe pas encore (avant migration) ou en cas
    d'erreur DB, renvoie None au lieu de casser le rendu (ex. healthcheck).
    """
    try:
        from apps.adminpanel.models import SiteSetting
        return {"site": SiteSetting.load()}
    except Exception:
        return {"site": None}

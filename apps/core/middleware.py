"""Mode maintenance piloté par l'interrupteur « Mode maintenance » du panel admin
(Paramètres > Affichage, champ SiteSetting.maintenance_mode).

Interrupteur actif : le site public n'affiche plus que « En mode maintenance »,
pour TOUT le monde — visiteurs comme comptes connectés, administrateurs compris
(page core/maintenance.html en 503 + Retry-After, que les moteurs traitent comme
une indisponibilité temporaire ; JSON 503 sur l'API publique). Le mode ne se lève
que depuis le panel admin, par un administrateur : restent donc ouverts le panel et
sa connexion, l'admin Django, les statiques/médias, la sonde de santé, et les
appels serveur-à-serveur des fournisseurs de paiement (un encaissement ne doit
jamais être perdu pendant une maintenance).
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.loader import render_to_string

_ALWAYS_OPEN = (
    "/dashboard/",
    "/login/",
    "/logout/",
    "/django-admin/",
    "/static/",
    "/media/",
    "/health/",
    "/api/webhook/",
    "/api/paiement/confirm-manual/",
)


def maintenance_enabled() -> bool:
    try:
        from apps.adminpanel.models import SiteSetting

        return SiteSetting.objects.filter(pk=1, maintenance_mode=True).exists()
    except Exception:
        # Table absente (avant migration) ou base indisponible : on ne ferme jamais
        # le site sur une erreur, la maintenance doit être voulue.
        return False


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path_info.startswith(_ALWAYS_OPEN) or not maintenance_enabled():
            return self.get_response(request)
        if request.path_info.startswith("/api/"):
            response = JsonResponse({"ok": False, "error": "En mode maintenance"}, status=503)
        else:
            response = HttpResponse(render_to_string("core/maintenance.html"), status=503)
        response["Retry-After"] = "3600"
        return response

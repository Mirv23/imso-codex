"""Mode maintenance piloté par l'interrupteur « Mode maintenance » du panel admin
(Paramètres > Affichage, champ SiteSetting.maintenance_mode).

Interrupteur actif : les visiteurs reçoivent la page de maintenance en 503 +
Retry-After (les moteurs y voient une indisponibilité TEMPORAIRE, pas un contenu à
indexer) et l'API publique répond 503 en JSON. Restent ouverts :
- le personnel connecté (is_staff), qui continue de voir le vrai site pour le
  vérifier — le bandeau core/partials/maintenance_banner.html le lui rappelle ;
- ce qui sert à administrer et à faire tourner le site : panel admin et sa
  connexion, admin Django, statiques/médias, sonde de santé, et les appels
  serveur-à-serveur des fournisseurs de paiement (un encaissement ne doit jamais
  être perdu pendant une maintenance).
"""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

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
    """À placer APRÈS `AuthenticationMiddleware` dans MIDDLEWARE (lit request.user)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path_info.startswith(_ALWAYS_OPEN) or not maintenance_enabled():
            return self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_staff:
            return self.get_response(request)
        if request.path_info.startswith("/api/"):
            response = JsonResponse(
                {"ok": False, "error": "Site en maintenance. Merci de réessayer un peu plus tard."},
                status=503,
            )
        else:
            response = render(request, "core/maintenance.html", status=503)
        response["Retry-After"] = "3600"
        return response

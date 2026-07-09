"""Contrôle d'accès du panneau admin.

Règle unique : le panneau et son API ne sont accessibles qu'au personnel
(`is_staff`). Un simple compte authentifié (ex. futur compte client de la
boutique) ne doit JAMAIS pouvoir atteindre ces vues.

- `staff_required`      : décorateur pour les vues fonctions (API v1 JSON).
- `StaffRequiredMixin`  : mixin pour les vues classes (dashboard).
- `IsStaff`             : permission DRF pour l'API v2.
"""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission

_FORBIDDEN_MESSAGE = "Accès réservé au personnel administrateur."


def _is_api_request(request: HttpRequest) -> bool:
    """Requête censée recevoir du JSON (endpoint /dashboard/api/*, XHR, ou Accept
    JSON) : on ne doit PAS lui renvoyer une redirection 302 vers une page HTML."""
    return (
        "/api/" in request.path
        or request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def staff_required(view_func):
    """Autorise uniquement les utilisateurs `is_staff`.

    - Anonyme, appel API → 401 JSON (sinon fetch suit la 302 vers /login/ et
      recoit une page HTML 200 -> dashboard vide silencieux / faux succes).
    - Anonyme, page HTML → redirection vers la connexion (avec `next`).
    - Connecté non-staff → 403 JSON.
    """

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            if _is_api_request(request):
                return JsonResponse({"error": "Session expirée, veuillez vous reconnecter."}, status=401)
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")
        if not user.is_staff:
            return JsonResponse({"error": _FORBIDDEN_MESSAGE}, status=403)
        # Contrôle par section pour les admins simples (non super-admin) : ils
        # n'accèdent qu'aux sections que le super-admin leur a attribuées.
        # Fail-closed : une section inconnue ou « admins » est refusée.
        if not user.is_superuser:
            from .sections import section_for_urlname, user_can

            url_name = getattr(getattr(request, "resolver_match", None), "url_name", None)
            section = section_for_urlname(url_name)
            if not user_can(user, section):
                return JsonResponse(
                    {"error": "Vous n'avez pas accès à cette section."}, status=403
                )
        return view_func(request, *args, **kwargs)

    return _wrapped


class StaffRequiredMixin(AccessMixin):
    """Rend une vue classe accessible uniquement au personnel (`is_staff`).

    Anonyme OU connecté non-staff → redirection vers la connexion admin (avec
    `next`). On redirige plutôt que renvoyer un 403 sec : la session est partagée
    avec la plateforme de formation, donc un étudiant/prof connecté qui clique un
    lien vers le dashboard doit pouvoir se reconnecter en administrateur.
    """

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated and user.is_staff):
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")
        return super().dispatch(request, *args, **kwargs)


class IsStaff(BasePermission):
    """Permission DRF : réservé au personnel (`is_staff`)."""

    message = _FORBIDDEN_MESSAGE

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
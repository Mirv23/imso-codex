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


def staff_required(view_func):
    """Autorise uniquement les utilisateurs `is_staff`.

    - Anonyme          → redirection vers la page de connexion (avec `next`).
    - Connecté non-staff → 403 JSON (le dashboard consomme du JSON).
    """

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")
        if not user.is_staff:
            return JsonResponse({"error": _FORBIDDEN_MESSAGE}, status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped


class StaffRequiredMixin(AccessMixin):
    """Rend une vue classe accessible uniquement au personnel (`is_staff`).

    Anonyme → redirection login ; connecté non-staff → 403 (PermissionDenied,
    via le comportement standard d'`AccessMixin.handle_no_permission`).
    """

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated and user.is_staff):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class IsStaff(BasePermission):
    """Permission DRF : réservé au personnel (`is_staff`)."""

    message = _FORBIDDEN_MESSAGE

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_staff)
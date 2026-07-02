"""Journalisation d'audit des actions du personnel.

Fonctionnement :
- `AuditUserMiddleware` mémorise l'utilisateur de la requête courante dans un
  thread-local ;
- des signaux `post_save`/`post_delete` sur les modèles métier créent une entrée
  `AuditLog` — mais **uniquement** si l'action est réalisée par un membre du
  personnel (`is_staff`). Les créations issues des formulaires publics (visiteur
  anonyme) ne sont donc pas journalisées ici (elles le sont déjà comme données +
  notifications).

Couvre à la fois l'API v1, l'API v2 (DRF) et l'admin Django, sans toucher aux
vues, puisque tout passe par les signaux ORM.
"""

from __future__ import annotations

import threading

_state = threading.local()


def set_current_user(user) -> None:
    _state.user = user


def get_current_user():
    return getattr(_state, "user", None)


class AuditUserMiddleware:
    """Expose l'utilisateur de la requête aux signaux (via thread-local).

    À placer APRÈS `AuthenticationMiddleware` dans MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)


def _record(action: str, instance) -> None:
    user = get_current_user()
    if not (user and getattr(user, "is_authenticated", False) and getattr(user, "is_staff", False)):
        return
    from .models import AuditLog

    AuditLog.objects.create(
        user=user,
        username=user.get_username(),
        action=action,
        model_name=type(instance).__name__,
        object_id=str(getattr(instance, "pk", "") or ""),
        object_label=str(instance)[:200],
    )


def _on_save(sender, instance, created, **kwargs) -> None:
    _record(AuditLogAction.CREATE if created else AuditLogAction.UPDATE, instance)


def _on_delete(sender, instance, **kwargs) -> None:
    _record(AuditLogAction.DELETE, instance)


# Constantes locales pour éviter d'importer les modèles au chargement du module.
class AuditLogAction:
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


def connect() -> None:
    """Branche les signaux d'audit. Appelé depuis AppConfig.ready()."""
    from django.db.models.signals import post_delete, post_save

    from .models import (
        ContactRequest,
        Course,
        Enrollment,
        GEI,
        Member,
        Order,
        Payment,
        PaymentProvider,
        Product,
        Testimonial,
        VenueBooking,
    )

    audited = [
        Member,
        Course,
        GEI,
        PaymentProvider,
        Payment,
        VenueBooking,
        Enrollment,
        Testimonial,
        ContactRequest,
        Product,
        Order,
    ]
    for model in audited:
        post_save.connect(_on_save, sender=model, dispatch_uid=f"audit_save_{model.__name__}")
        post_delete.connect(_on_delete, sender=model, dispatch_uid=f"audit_delete_{model.__name__}")

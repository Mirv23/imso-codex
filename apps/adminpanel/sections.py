"""Catalogue des sections du panel admin et résolution des permissions.

Un super-administrateur (User.is_superuser) accède à tout. Un administrateur
simple (is_staff, non superuser) n'accède qu'aux sections que le super-admin lui
a attribuées (modèle AdminAccess.sections). Le contrôle serveur est centralisé
dans `staff_required` (permissions.py) et repose sur `section_for_urlname` +
`user_can` définis ici. Politique fail-closed : une section inconnue est refusée
à un admin simple.
"""

from __future__ import annotations

# Libellés lisibles des sections (pour l'UI d'attribution des droits).
SECTION_LABELS: dict[str, str] = {
    "dashboard": "Tableau de bord",
    "members": "Membres",
    "geis": "GEIs",
    "courses": "Cours & chapitres",
    "teachers": "Professeurs (KYC)",
    "students": "Étudiants & inscriptions formation",
    "enrollments": "Inscriptions (site public)",
    "bookings": "Réservations de salle",
    "payments": "Paiements",
    "contacts": "Messages de contact",
    "providers": "Moyens de paiement",
    "testimonials": "Témoignages",
    "products": "Boutique / Produits",
    "orders": "Commandes",
    "blog": "Blog",
    "values": "Nos valeurs (site)",
    "steps": "Notre processus (site)",
    "sitetexts": "Textes du site",
    "siteimages": "Images du site",
    "settings": "Paramètres du site",
    "export": "Exports CSV",
    "admins": "Administrateurs",
}

# Sections attribuables à un admin simple (exclut « dashboard » toujours dispo et
# « admins » réservé aux super-administrateurs).
GRANTABLE_SECTIONS: list[str] = [k for k in SECTION_LABELS if k not in ("dashboard", "admins")]

# url_name toujours accessibles à tout membre du personnel (coquille du dashboard,
# entête, listes déroulantes partagées) — jamais gatés par section.
ALWAYS_ALLOWED: set[str] = {
    "dashboard", "summary", "summary-v1", "charts", "audit-log",
    "notification-list", "notification-list-v1",
    "notification-check", "notification-check-v1",
    "notification-read", "notification-read-v1",
    "notification-read-all", "notification-read-all-v1",
    "teacher-options",
}

# Résolution url_name -> section. Ordre important : préfixes les plus spécifiques
# d'abord (ex. « course-enrollment » avant « course »).
_PREFIX_MAP: list[tuple[str, str]] = [
    ("course-enrollment", "students"),
    ("student", "students"),
    ("chapter", "courses"),
    ("course", "courses"),
    ("member", "members"),
    ("learner", "teachers"),
    ("teacher", "teachers"),
    ("booking", "bookings"),
    ("payment", "payments"),
    ("contact", "contacts"),
    ("gei", "geis"),
    ("provider", "providers"),
    ("enrollment", "enrollments"),
    ("testimonial", "testimonials"),
    ("product", "products"),
    ("order", "orders"),
    ("blog", "blog"),
    ("settings", "settings"),
    ("core-value", "values"),
    ("process-step", "steps"),
    ("site-text", "sitetexts"),
    ("site-image", "siteimages"),
    ("export", "export"),
    ("admin", "admins"),
]


def section_for_urlname(name: str | None) -> str | None:
    """Section requise pour ce url_name. None = toujours permis (staff).
    '__unknown__' = non répertorié -> refusé à un admin simple (fail-closed)."""
    if not name or name in ALWAYS_ALLOWED:
        return None
    if name.startswith("upload"):
        return None  # upload-image : permis à tout staff (raffinable par cible)
    for prefix, section in _PREFIX_MAP:
        if name.startswith(prefix):
            return section
    return "__unknown__"


def user_sections(user) -> set[str]:
    """Ensemble des sections accessibles à cet utilisateur."""
    if getattr(user, "is_superuser", False):
        return set(SECTION_LABELS)
    try:
        return set(user.admin_access.sections or [])
    except Exception:
        return set()


def user_can(user, section: str | None) -> bool:
    """Cet utilisateur peut-il accéder à la section requise ?"""
    if section is None:
        return True
    if getattr(user, "is_superuser", False):
        return True
    if section in ("admins", "__unknown__"):
        return False  # gestion des admins = super-admin uniquement ; inconnu = refus
    return section in user_sections(user)

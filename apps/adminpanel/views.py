from __future__ import annotations

import csv
import json
import logging
import os
from datetime import timedelta
from typing import Any, Callable, Generator

from django.contrib.auth import get_user_model, logout as auth_logout
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import validate_email
from django.db.models import Count, Max, Sum, Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit
from django.conf import settings

logger = logging.getLogger(__name__)

from .permissions import StaffRequiredMixin, staff_required
from .models import (
    AdminAccess,
    AdminNotification,
    AuditLog,
    BlogPost,
    Chapter,
    ChapterCompletion,
    ContactRequest,
    Course,
    CoreValue,
    EncryptedCharField,
    Enrollment,
    GEI,
    Member,
    Order,
    CourseEnrollment,
    Payment,
    PaymentProvider,
    Product,
    ProcessStep,
    Profile,
    SiteImage,
    SiteSetting,
    SiteText,
    Testimonial,
    VenueBooking,
)

User = get_user_model()


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
@method_decorator(ratelimit(key="post:username", rate="5/m", method="POST", block=True), name="post")
class RateLimitedLoginView(LoginView):
    """Login admin avec limitation anti-force-brute (par IP et par identifiant)."""

    template_name = "adminpanel/login.html"
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        # On ne saute le formulaire (redirect_authenticated_user) que si l'utilisateur
        # est DÉJÀ administrateur. Un compte non-staff (étudiant/prof de la plateforme
        # de formation, session partagée) doit voir le formulaire pour se reconnecter
        # en admin — sinon on aurait une boucle /login/ -> /dashboard/ (403) -> /login/.
        if request.user.is_authenticated and not request.user.is_staff:
            self.redirect_authenticated_user = False
        return super().dispatch(request, *args, **kwargs)


def logout_view(request: HttpRequest) -> HttpResponse:
    """Deconnexion admin acceptant GET et POST.

    Le lien « Deconnexion » de la barre laterale est un <a> (GET) ; or la
    LogoutView de Django 5.2 n'accepte que POST -> 405. On gere donc GET+POST
    ici et on renvoie vers la page de login.
    """
    from django.shortcuts import redirect

    auth_logout(request)
    return redirect(settings.LOGIN_URL)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/simple_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Le panel admin ne doit jamais etre servi depuis le cache navigateur :
        # sinon une ancienne version (mise en cache disque avant un deploiement)
        # continue de s'afficher. On force un rechargement a chaque visite.
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["summary"] = get_dashboard_summary()
        context["django_version"] = "5.2.15"
        # Permissions du user courant + catalogue des sections attribuables :
        # le front masque les sections non autorisees et alimente le formulaire
        # d'attribution des droits (section Administrateurs).
        from .sections import SECTION_LABELS, GRANTABLE_SECTIONS, user_sections
        u = self.request.user
        context["me_is_superuser"] = bool(u.is_superuser)
        context["me_sections_json"] = json.dumps(sorted(user_sections(u)))
        context["grantable_sections_json"] = json.dumps(
            [{"key": k, "label": SECTION_LABELS[k]} for k in GRANTABLE_SECTIONS]
        )
        return context


_COLORS = ["#2D6A4F", "#1B4332", "#40916C", "#52B788", "#74C69D", "#95D5B2"]
_AVATAR_CLASSES = ["warm", "blue", "purple", "teal", "rose", "amber"]
_GEI_CODES: dict[int, str] = {}
_GEI_COLORS = ["#2D6A4F", "#E67E22", "#2980B9", "#8E44AD", "#16A085", "#C0392B", "#D35400"]


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return (parts[0][:2]).upper() if parts else ""


def _status_label(status: str) -> str:
    return {"active": "Actif", "paused": "Attente", "alumni": "Suspendu", "prospect": "Prospect"}.get(status, status)


def _relative_time(dt) -> str:
    if not dt:
        return ""
    now = timezone.now()
    diff = now - dt
    if diff < timedelta(minutes=1):
        return "il y a quelques secondes"
    if diff < timedelta(hours=1):
        m = int(diff.total_seconds() / 60)
        return f"il y a {m} min"
    if diff < timedelta(days=1):
        h = int(diff.total_seconds() / 3600)
        return f"il y a {h}h"
    if diff < timedelta(days=7):
        d = diff.days
        return f"il y a {d}j"
    return dt.strftime("%d %b %Y")


def _month_abbr(dt) -> str:
    months = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    return months[dt.month]


def _get_gei_code(gei_id: int | None) -> str:
    if gei_id is None:
        return ""
    if gei_id not in _GEI_CODES:
        try:
            g = GEI.objects.get(pk=gei_id)
            _GEI_CODES[gei_id] = g.city.upper()[:3]
        except GEI.DoesNotExist:
            _GEI_CODES[gei_id] = ""
    return _GEI_CODES[gei_id]


def _prefetch_gei_codes() -> None:
    for g in GEI.objects.all():
        _GEI_CODES[g.pk] = g.city.upper()[:3]


def _serialize_members_for_react() -> list[dict[str, Any]]:
    _prefetch_gei_codes()
    qs = Member.objects.select_related("gei").all()[:50]
    result = []
    for i, m in enumerate(qs):
        name = f"{m.first_name} {m.last_name}"
        gei_code = _get_gei_code(m.gei_id) if m.gei_id else ""
        result.append({
            "id": str(m.pk),
            "name": name,
            "email": m.email or "",
            "gei": gei_code,
            "status": _status_label(m.status),
            "date": m.created_at.strftime("%d %b %Y") if m.created_at else "",
            "avatar": _AVATAR_CLASSES[i % len(_AVATAR_CLASSES)],
            "initials": _initials(name),
            "phone": m.phone or "",
        })
    return result


def _serialize_payments_for_react() -> list[dict[str, Any]]:
    # venue_booking inclus : la boucle y accede (l.192) -> sans lui, 1 requete
    # par paiement de reservation (N+1).
    qs = Payment.objects.select_related(
        "provider", "enrollment__member", "enrollment__course", "venue_booking"
    ).all()[:20]
    result = []
    for p in qs:
        member_name = p.payer_name
        course_title = ""
        if p.enrollment and p.enrollment.course:
            course_title = p.enrollment.course.title
        elif p.purpose == "venue" and p.venue_booking:
            course_title = f"Réservation: {p.venue_booking.event_type}"
        elif p.purpose == "course" and p.notes:
            # Paiement formation materialise (pas de FK Enrollment) : libelle depuis notes.
            course_title = p.notes

        provider_type = p.provider.provider_type if p.provider else "manual"
        method = {"moncash": "MonCash", "stripe": "Stripe", "natcash": "NatCash",
                   "bank": "Virement", "cash": "Cash", "manual": "Manuel"}.get(provider_type, "Autre")

        status = {"paid": "Réussi", "pending": "En attente", "failed": "Échoué",
                   "refunded": "Remboursé", "cancelled": "Annulé"}.get(p.status, p.status)

        result.append({
            "id": str(p.pk),
            "member": member_name,
            "course": course_title,
            "amount": p.amount_htg,
            "method": method,
            "status": status,
            "date": _relative_time(p.created_at),
        })
    return result


def _serialize_courses_for_react() -> list[dict[str, Any]]:
    qs = Course.objects.annotate(enrollment_count=Count("enrollments")).all()[:20]
    pks = [c.pk for c in qs]
    revenues = Payment.objects.filter(
        enrollment__course_id__in=pks,
        status=Payment.Status.PAID,
    ).values("enrollment__course_id").annotate(total=Sum("amount_htg"))
    rev_map = {r["enrollment__course_id"]: r["total"] for r in revenues}
    result = []
    for i, c in enumerate(qs):
        result.append({
            "id": str(c.pk),
            "title": c.title,
            "students": c.enrollment_count or 0,
            "revenue": rev_map.get(c.pk, 0),
            "status": c.is_active,
            "thumb": _AVATAR_CLASSES[i % len(_AVATAR_CLASSES)],
            "cat": c.category or "",
            "duration": "",
            "price": c.price_htg,
        })
    return result


def _serialize_revenue_for_react() -> list[dict[str, Any]]:
    now = timezone.now()
    # Reculer mois par mois sur le calendrier reel. Un pas de 30 jours duplique
    # ou saute des mois (fevrier, mois de 31 jours) -> labels dupliques dans le
    # graphique et delta mois-sur-mois errone (compare parfois un mois a lui-meme).
    months = []
    y, m = now.year, now.month
    for _ in range(6):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    months.reverse()

    result = []
    for (yy, mm) in months:
        total = Payment.objects.filter(
            status=Payment.Status.PAID,
            created_at__year=yy,
            created_at__month=mm,
        ).aggregate(total=Sum("amount_htg"))["total"] or 0
        result.append({
            "m": _month_abbr(now.replace(year=yy, month=mm, day=1)),
            "v": total,
        })
    return result


def _serialize_categories_for_react() -> list[dict[str, Any]]:
    qs = Course.objects.values("category").annotate(cnt=Count("id")).order_by("-cnt")
    total = sum(item["cnt"] for item in qs) or 1
    result = []
    for i, item in enumerate(qs):
        if not item["category"]:
            continue
        result.append({
            "name": item["category"],
            "value": round(item["cnt"] / total * 100),
            "color": _COLORS[i % len(_COLORS)],
        })
    return result


def _serialize_notifs_for_react() -> list[dict[str, Any]]:
    qs = AdminNotification.objects.all()[:20]
    result = []
    for n in qs:
        result.append({
            "id": n.pk,
            "msg": n.message,
            "time": _relative_time(n.created_at),
            "read": n.is_read,
        })
    return result


def _get_page_params(request: HttpRequest) -> tuple[int, int, int]:
    try:
        page = int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = int(request.GET.get("per_page", 20))
    except (ValueError, TypeError):
        per_page = 20
    # Borne basse a 1 : per_page=0 (ou negatif) donnerait une ZeroDivisionError
    # au calcul de total_pages -> 500.
    per_page = max(1, min(per_page, 100))
    page = max(page, 1)
    offset = (page - 1) * per_page
    return page, per_page, offset


def _paginated_response(queryset: QuerySet, request: HttpRequest, serializer: Callable[[Any], dict[str, Any]]) -> JsonResponse:
    page, per_page, offset = _get_page_params(request)
    total = queryset.count()
    items = list(map(serializer, queryset[offset: offset + per_page]))
    return JsonResponse({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
    })


def _json_body(request: HttpRequest) -> dict[str, Any]:
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError, ValueError):
        return {}
    # Un corps JSON valide mais non-objet ([], 5, "x") ferait planter les .get()
    # ensuite (AttributeError -> 500). On ne renvoie qu'un dict.
    return data if isinstance(data, dict) else {}


def _error(msg: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": msg}, status=status)


def _safe_date(raw):
    """Parse une date en ignorant tout ce qui est invalide OU hors-plage.

    parse_date() LEVE ValueError sur '2026-13-45' au lieu de renvoyer None :
    ce helper protege les filtres de liste d'un 500.
    """
    from django.utils.dateparse import parse_date
    try:
        return parse_date(str(raw or "")) or None
    except (ValueError, TypeError):
        return None


def _ok() -> JsonResponse:
    return JsonResponse({"ok": True})


def _deletion_block_reason(instance: Any) -> str | None:
    """Retourne un message si la suppression est dangereuse (données liées), sinon None.

    Évite les suppressions destructrices : un membre supprimé efface en cascade
    ses inscriptions ; un GEI/cours/fournisseur supprimé casse des liens. On
    conseille plutôt de désactiver (statut) que de supprimer.
    """
    # Les membres sont supprimables sans restriction (demande explicite) : la
    # suppression supprime en cascade leurs inscriptions ; les paiements liés sont
    # conservés (leur lien vers l'inscription passe simplement à NULL).
    if isinstance(instance, GEI):
        if instance.members.exists():
            return "Des membres sont rattachés à ce GEI. Désactivez-le plutôt que de le supprimer."
    elif isinstance(instance, Course):
        if instance.enrollments.exists():
            return "Ce cours a des inscriptions. Désactivez-le plutôt que de le supprimer."
    elif isinstance(instance, PaymentProvider):
        if instance.payments.exists():
            return "Ce fournisseur est lié à des paiements. Désactivez-le plutôt que de le supprimer."
    return None


_MEMBER_MAXLEN = {"first_name": 80, "last_name": 80, "phone": 40, "email": 254}
_MEMBER_LABELS = {"first_name": "Le prénom", "last_name": "Le nom", "phone": "Le téléphone"}


def _clean_member_data(data: dict, *, partial: bool) -> tuple[dict[str, Any] | None, str | None]:
    """Valide et normalise le payload d'un membre. Retourne (cleaned, erreur).

    Empêche les 500 (longueurs, types, FK inexistante, valeurs négatives) et les
    données incohérentes (statut hors choix, email invalide, champ requis vide).
    `partial=True` (édition PUT) ne valide que les champs réellement fournis.
    """
    cleaned: dict[str, Any] = {}

    # Champs texte requis (prénom, nom, téléphone)
    for f in ("first_name", "last_name", "phone"):
        if f in data or not partial:
            val = str(data.get(f) or "").strip()
            if not val:
                return None, f"{_MEMBER_LABELS[f]} est obligatoire."
            if len(val) > _MEMBER_MAXLEN[f]:
                return None, f"{_MEMBER_LABELS[f]} ne peut pas dépasser {_MEMBER_MAXLEN[f]} caractères."
            cleaned[f] = val

    # Email (optionnel mais validé si fourni)
    if "email" in data:
        email = str(data.get("email") or "").strip()
        if email:
            if len(email) > _MEMBER_MAXLEN["email"]:
                return None, "L'adresse email est trop longue."
            try:
                validate_email(email)
            except ValidationError:
                return None, "L'adresse email n'est pas valide."
        cleaned["email"] = email

    # Statut (doit appartenir aux choix)
    if "status" in data:
        status = data.get("status") or Member.Status.PROSPECT
        if status not in Member.Status.values:
            return None, "Statut invalide."
        cleaned["status"] = status
    elif not partial:
        cleaned["status"] = Member.Status.PROSPECT

    # Date d'adhésion ('' -> None)
    if "joined_at" in data:
        cleaned["joined_at"] = data.get("joined_at") or None

    # Épargne mensuelle (entier >= 0)
    if "monthly_saving_htg" in data:
        raw = data.get("monthly_saving_htg")
        try:
            saving = int(raw) if raw not in (None, "") else 0
        except (ValueError, TypeError):
            return None, "L'épargne mensuelle doit être un nombre."
        if saving < 0:
            return None, "L'épargne mensuelle ne peut pas être négative."
        cleaned["monthly_saving_htg"] = saving
    elif not partial:
        cleaned["monthly_saving_htg"] = 0

    # GEI (FK optionnelle, doit exister si fournie)
    if "gei_id" in data or "gei" in data:
        gid = data.get("gei_id") or data.get("gei") or None
        if gid:
            try:
                gid = int(gid)
            except (ValueError, TypeError):
                return None, "GEI invalide."
            if not GEI.objects.filter(pk=gid).exists():
                return None, "Le GEI sélectionné n'existe pas."
        cleaned["gei_id"] = gid
    elif not partial:
        cleaned["gei_id"] = None

    return cleaned, None


@staff_required
@require_http_methods(["POST"])
def member_create(request: HttpRequest) -> JsonResponse:
    cleaned, err = _clean_member_data(_json_body(request), partial=False)
    if err:
        return _error(err)
    m = Member.objects.create(**cleaned)
    logger.info("Member %d created by user %s (%s %s)", m.pk, request.user.username, m.first_name, m.last_name)
    return JsonResponse(_serialize_member(m), status=201)


# ── Members ──────────────────────────────────────────────

def _serialize_member(m: Member) -> dict[str, Any]:
    gei = m.gei
    return {
        "id": m.pk,
        "first_name": m.first_name,
        "last_name": m.last_name,
        "email": m.email,
        "phone": m.phone,
        "gei_id": m.gei_id,
        "gei__name": gei.name if gei else None,
        "gei__city": gei.city if gei else None,
        "status": m.status,
        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        "monthly_saving_htg": m.monthly_saving_htg,
        "created_at": m.created_at.isoformat(),
    }


def _filtered_members(request: HttpRequest) -> QuerySet:
    """Queryset des membres avec recherche/filtres/tri appliqués (partagé)."""
    qs = Member.objects.select_related("gei").all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )
    gei = request.GET.get("gei")
    if gei and str(gei).isdigit():
        qs = qs.filter(gei_id=gei)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    sort_map = {
        "recent": ("-created_at",),
        "oldest": ("created_at",),
        "name": ("last_name", "first_name"),
        "savings": ("-monthly_saving_htg",),
        "savings_asc": ("monthly_saving_htg",),
    }
    return qs.order_by(*sort_map.get(request.GET.get("sort"), ("-created_at",)))


@staff_required
def member_list(request: HttpRequest) -> JsonResponse:
    return _paginated_response(_filtered_members(request), request, _serialize_member)


@staff_required
def member_overview(request: HttpRequest) -> JsonResponse:
    """Vue Membres en UN seul appel : liste paginée + stats globales + GEIs.

    Évite les 4 requêtes réseau séparées (liste, graphiques, résumé, GEIs) qui
    ralentissaient l'affichage de la section, surtout au démarrage à froid Vercel.
    """
    qs = _filtered_members(request)
    page, per_page, offset = _get_page_params(request)
    total = qs.count()
    items = [_serialize_member(m) for m in qs[offset: offset + per_page]]
    status_counts = {
        row["status"]: row["c"]
        for row in Member.objects.values("status").annotate(c=Count("id"))
    }
    # Stats du GEI ciblé (panneau « membres du groupe ») — calculées sur TOUT le
    # GEI (indépendant de la pagination). null si aucun ?gei= (section Membres intacte).
    gei_param = request.GET.get("gei")
    gei_stats = None
    if gei_param and str(gei_param).isdigit():
        scoped = Member.objects.filter(gei_id=int(gei_param))
        gei_stats = {
            "total": scoped.count(),
            "active": scoped.filter(status="active").count(),
            "savings": scoped.aggregate(s=Sum("monthly_saving_htg"))["s"] or 0,
        }
    # Agrégats par GEI sur TOUT le queryset filtré (pas seulement la page) : la
    # vue « Par GEI » affiche ainsi des compteurs/épargne EXACTS même au-delà de
    # 100 membres (sinon la somme des items paginés est fausse).
    gei_groups = list(
        qs.values("gei_id", "gei__name", "gei__city")
        .annotate(count=Count("id"), savings=Sum("monthly_saving_htg"))
        .order_by("gei__city", "gei__name")
    )
    return JsonResponse({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
        "gei_stats": gei_stats,
        "gei_groups": gei_groups,
        "stats": {
            "total": sum(status_counts.values()),
            "active": status_counts.get("active", 0),
            "prospect": status_counts.get("prospect", 0),
            "paused": status_counts.get("paused", 0),
            "alumni": status_counts.get("alumni", 0),
            "savings": Member.objects.aggregate(s=Sum("monthly_saving_htg"))["s"] or 0,
        },
        "geis": list(
            GEI.objects.filter(is_active=True).values("id", "name", "city").order_by("city", "name")
        ),
    })


@staff_required
def member_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        m = Member.objects.select_related("gei").get(pk=pk)
    except Member.DoesNotExist:
        return _error("Member not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_member(m))
    elif request.method == "PUT":
        cleaned, err = _clean_member_data(_json_body(request), partial=True)
        if err:
            return _error(err)
        for field, val in cleaned.items():
            setattr(m, field, val)
        m.save()
        logger.info("Member %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_member(m))
    elif request.method == "DELETE":
        reason = _deletion_block_reason(m)
        if reason:
            return _error(reason, 409)
        logger.info("Member %d deleted by user %s", pk, request.user.username)
        m.delete()
        return _ok()
    return _error("Method not allowed", 405)


@staff_required
def member_profile(request: HttpRequest, pk: int) -> JsonResponse:
    """Fiche membre : coordonnées + inscriptions et paiements liés (lecture seule).

    Les paiements d'un membre sont rattachés INDIRECTEMENT via ses inscriptions
    (Payment.enrollment -> Enrollment.member). On ne sert aucune capture/PII de
    paiement (screenshot privé exclu), uniquement les métadonnées de suivi.
    """
    try:
        m = Member.objects.select_related("gei").get(pk=pk)
    except Member.DoesNotExist:
        return _error("Member not found", 404)

    enrollments = (
        Enrollment.objects.select_related("course")
        .filter(member=m)
        .order_by("-created_at")
    )
    payments = (
        Payment.objects.select_related("enrollment__course")
        .filter(enrollment__member=m)
        .order_by("-created_at")
    )
    return JsonResponse({
        "member": _serialize_member(m),
        "enrollments": [
            {
                "id": e.pk,
                "status": e.status,
                "course_title": e.course.title if e.course else None,
                "course_category": e.course.category if e.course else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in enrollments
        ],
        "payments": [
            {
                "id": p.pk,
                "reference": p.reference,
                "purpose": p.purpose,
                "status": p.status,
                "amount_htg": p.amount_htg,
                "course_title": (
                    p.enrollment.course.title
                    if p.enrollment and p.enrollment.course else None
                ),
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
        "totals": {
            "enrollments": enrollments.count(),
            "payments": payments.count(),
            "paid_htg": (
                payments.filter(status=Payment.Status.PAID)
                .aggregate(s=Sum("amount_htg"))["s"] or 0
            ),
        },
    })


# ── Courses ──────────────────────────────────────────────

def _serialize_course(c: Course, enroll_count: int | None = None) -> dict[str, Any]:
    if enroll_count is None:
        enroll_count = getattr(c, 'enrollment_count', c.enrollments.count())
    chap = getattr(c, 'chapter_count', None)
    if chap is None:
        chap = c.chapters.count()
    return {
        "id": c.pk,
        "title": c.title,
        "category": c.category,
        "instructor": c.instructor,
        "city": c.city,
        "price_htg": c.price_htg,
        "capacity": c.capacity,
        "is_active": c.is_active,
        "public_slug": c.public_slug,
        "description": c.description,
        "level": c.level,
        "banner": c.banner.url if c.banner else "",
        "teacher": c.teacher_id,
        "teacher_name": (c.teacher.get_full_name() or c.teacher.username) if c.teacher else "",
        "enrollment_count": enroll_count,
        "chapter_count": chap,
        "created_at": c.created_at.isoformat(),
    }


def _serialize_chapter(ch: Chapter) -> dict[str, Any]:
    return {
        "id": ch.pk,
        "course_id": ch.course_id,
        "title": ch.title,
        "position": ch.position,
        "description": ch.description,
        "duration_minutes": ch.duration_minutes,
        "video": ch.video.url if ch.video else "",
        "has_video": bool(ch.video),
    }


def _filtered_courses(request: HttpRequest) -> QuerySet:
    qs = Course.objects.select_related("teacher").annotate(
        enrollment_count=Count("enrollments", distinct=True),
        chapter_count=Count("chapters", distinct=True),
    ).all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(instructor__icontains=search)
            | Q(category__icontains=search)
        )
    category = request.GET.get("category")
    if category:
        qs = qs.filter(category=category)
    active = request.GET.get("active")
    if active in ("1", "0", "true", "false"):
        qs = qs.filter(is_active=active in ("1", "true"))
    sort_map = {
        "recent": ("-created_at",),
        "title": ("title",),
        "price": ("-price_htg",),
        "price_asc": ("price_htg",),
        "enrollments": ("-enrollment_count",),
    }
    return qs.order_by(*sort_map.get(request.GET.get("sort"), ("-created_at",)))


@staff_required
def course_list(request: HttpRequest) -> JsonResponse:
    return _paginated_response(_filtered_courses(request), request, _serialize_course)


@staff_required
def course_overview(request: HttpRequest) -> JsonResponse:
    """Vue Cours en un seul appel : liste paginée + stats + catégories."""
    qs = _filtered_courses(request)
    page, per_page, offset = _get_page_params(request)
    total = qs.count()
    items = [_serialize_course(c) for c in qs[offset: offset + per_page]]
    all_courses = Course.objects.all()
    return JsonResponse({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
        "stats": {
            "total": all_courses.count(),
            "active": all_courses.filter(is_active=True).count(),
            "inactive": all_courses.filter(is_active=False).count(),
            "enrollments": Enrollment.objects.count(),
            # KPI plateforme formation (CourseEnrollment).
            "students": CourseEnrollment.objects.count(),
            "active_access": CourseEnrollment.objects.filter(
                status=CourseEnrollment.Status.ACTIVE
            ).count(),
            "revenue_confirmed": CourseEnrollment.objects.filter(
                status=CourseEnrollment.Status.ACTIVE
            ).aggregate(s=Sum("course__price_htg"))["s"] or 0,
        },
        "categories": sorted(
            {c for c in all_courses.values_list("category", flat=True) if c}
        ),
    })


@staff_required
@require_http_methods(["GET"])
def course_students(request: HttpRequest, pk: int) -> JsonResponse:
    """Étudiants inscrits à un cours (roster de l'éditeur), avec progression."""
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return _error("Course not found", 404)
    total_chapters = course.chapters.count()
    qs = (
        CourseEnrollment.objects.filter(course=course)
        .select_related("student")
        .annotate(completed=Count(
            "student__chapter_completions",
            filter=Q(student__chapter_completions__chapter__course_id=pk),
            distinct=True,
        ))
        .order_by("-created_at")
    )
    items, active = [], 0
    for e in qs:
        if e.status == CourseEnrollment.Status.ACTIVE:
            active += 1
        completed = min(e.completed or 0, total_chapters)
        items.append({
            "id": e.pk,
            "student_name": e.student.get_full_name() or e.student.username,
            "student_email": e.student.email,
            "status": e.status,
            "completed_chapters": completed,
            "total_chapters": total_chapters,
            "progress_pct": round(completed / total_chapters * 100) if total_chapters else 0,
        })
    return JsonResponse({
        "items": items,
        "total": len(items),
        "active": active,
        "total_chapters": total_chapters,
        "price_htg": course.price_htg,
    })


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def course_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        c = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return _error("Course not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_course(c))
    elif request.method == "PUT":
        cleaned, err = _clean_course_data(_json_body(request), partial=True, exclude_pk=pk)
        if err:
            return _error(err)
        for fld, val in cleaned.items():
            setattr(c, fld, val)
        c.save()
        logger.info("Course %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_course(c))
    elif request.method == "DELETE":
        # Les inscriptions ADMIN (Enrollment) passent à NULL (SET_NULL), MAIS les
        # inscriptions ETUDIANTS de la plateforme /formation/ (CourseEnrollment) et
        # les chapitres sont en CASCADE : supprimer un cours détruirait alors la
        # progression de tous ses étudiants. On bloque dans ce cas.
        student_count = c.student_enrollments.count()
        if student_count:
            return _error(
                f"Ce cours a {student_count} étudiant(s) inscrit(s) sur la plateforme "
                "de formation. Désactivez-le (is_active=False) au lieu de le supprimer.",
                409,
            )
        logger.info("Course %d deleted by user %s", pk, request.user.username)
        c.delete()
        return _ok()


_COURSE_MAXLEN = {"title": 180, "category": 80, "instructor": 120, "city": 120, "public_slug": 200}
_COURSE_LABELS = {"title": "Le titre", "category": "La catégorie", "instructor": "Le formateur", "city": "La ville"}


def _clean_course_data(data: dict, *, partial: bool, exclude_pk: int | None = None):
    """Valide/normalise un cours. Retourne (cleaned, erreur).

    Empêche les 500 : longueurs, prix/capacité non-numériques ou négatifs, et
    surtout la collision de slug (public_slug="" est unique -> le 2e cours sans
    slug plantait). Un slug vide devient NULL (plusieurs NULL autorisés).
    """
    cleaned: dict[str, Any] = {}
    for f in ("title", "category", "instructor"):
        if f in data or not partial:
            val = str(data.get(f) or "").strip()
            if not val:
                return None, f"{_COURSE_LABELS[f]} est obligatoire."
            if len(val) > _COURSE_MAXLEN[f]:
                return None, f"{_COURSE_LABELS[f]} ne peut pas dépasser {_COURSE_MAXLEN[f]} caractères."
            cleaned[f] = val
    if "city" in data or not partial:
        city = str(data.get("city") or "").strip()
        if len(city) > _COURSE_MAXLEN["city"]:
            return None, "La ville ne peut pas dépasser 120 caractères."
        cleaned["city"] = city
    for f, label in (("price_htg", "Le prix"), ("capacity", "La capacité")):
        if f in data or not partial:
            raw = data.get(f)
            try:
                n = int(raw) if raw not in (None, "") else 0
            except (ValueError, TypeError):
                return None, f"{label} doit être un nombre."
            if n < 0:
                return None, f"{label} ne peut pas être négatif."
            cleaned[f] = n
    if "is_active" in data:
        cleaned["is_active"] = bool(data.get("is_active"))
    elif not partial:
        cleaned["is_active"] = True
    if "level" in data:
        level = str(data.get("level") or "").strip()
        if level and level not in Course.Level.values:
            return None, "Niveau invalide."
        cleaned["level"] = level
    if "description" in data:
        cleaned["description"] = str(data.get("description") or "")
    elif not partial:
        cleaned["description"] = ""
    if "teacher" in data or "teacher_id" in data:
        tid = data.get("teacher") if "teacher" in data else data.get("teacher_id")
        tid = tid or None
        if tid:
            try:
                tid = int(tid)
            except (ValueError, TypeError):
                return None, "Professeur invalide."
            if not Profile.objects.filter(user_id=tid, role=Profile.Role.TEACHER).exists():
                return None, "Ce professeur n'existe pas."
        cleaned["teacher_id"] = tid
    if "public_slug" in data or not partial:
        slug = str(data.get("public_slug") or "").strip()
        if len(slug) > _COURSE_MAXLEN["public_slug"]:
            return None, "Le slug public est trop long."
        if slug:
            dup = Course.objects.filter(public_slug=slug)
            if exclude_pk:
                dup = dup.exclude(pk=exclude_pk)
            if dup.exists():
                return None, "Ce slug public est déjà utilisé par un autre cours."
        cleaned["public_slug"] = slug or None
    return cleaned, None


@staff_required
@require_http_methods(["POST"])
def course_create(request: HttpRequest) -> JsonResponse:
    cleaned, err = _clean_course_data(_json_body(request), partial=False)
    if err:
        return _error(err)
    c = Course.objects.create(**cleaned)
    logger.info("Course %d created by user %s (%s)", c.pk, request.user.username, c.title)
    return JsonResponse(_serialize_course(c), status=201)


# ── Chapitres (contenu d'un cours) ───────────────────────

def _clean_chapter_data(data: dict, *, partial: bool):
    cleaned: dict[str, Any] = {}
    if "title" in data or not partial:
        title = str(data.get("title") or "").strip()
        if not title:
            return None, "Le titre du chapitre est obligatoire."
        if len(title) > 180:
            return None, "Le titre ne peut pas dépasser 180 caractères."
        cleaned["title"] = title
    if "description" in data:
        cleaned["description"] = str(data.get("description") or "")
    if "duration_minutes" in data:
        raw = data.get("duration_minutes")
        try:
            n = int(raw) if raw not in (None, "") else 0
        except (ValueError, TypeError):
            return None, "La durée doit être un nombre (en minutes)."
        if n < 0:
            return None, "La durée ne peut pas être négative."
        cleaned["duration_minutes"] = n
    return cleaned, None


@staff_required
@require_http_methods(["GET"])
def chapter_list(request: HttpRequest, course_pk: int) -> JsonResponse:
    if not Course.objects.filter(pk=course_pk).exists():
        return _error("Course not found", 404)
    chapters = Chapter.objects.filter(course_id=course_pk)  # ordonnés par position
    return JsonResponse({"items": [_serialize_chapter(ch) for ch in chapters]})


@staff_required
@require_http_methods(["POST"])
def chapter_create(request: HttpRequest, course_pk: int) -> JsonResponse:
    try:
        course = Course.objects.get(pk=course_pk)
    except Course.DoesNotExist:
        return _error("Course not found", 404)
    cleaned, err = _clean_chapter_data(_json_body(request), partial=False)
    if err:
        return _error(err)
    last = course.chapters.aggregate(m=Max("position"))["m"]
    cleaned["position"] = (last + 1) if last is not None else 0
    ch = Chapter.objects.create(course=course, **cleaned)
    logger.info("Chapter %d created on course %d by %s", ch.pk, course_pk, request.user.username)
    return JsonResponse(_serialize_chapter(ch), status=201)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def chapter_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        ch = Chapter.objects.get(pk=pk)
    except Chapter.DoesNotExist:
        return _error("Chapter not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_chapter(ch))
    if request.method == "PUT":
        cleaned, err = _clean_chapter_data(_json_body(request), partial=True)
        if err:
            return _error(err)
        for k, v in cleaned.items():
            setattr(ch, k, v)
        ch.save()
        return JsonResponse(_serialize_chapter(ch))
    ch.delete()
    return _ok()


@staff_required
@require_http_methods(["POST"])
def chapter_reorder(request: HttpRequest, course_pk: int) -> JsonResponse:
    """Réordonne les chapitres d'un cours à partir d'une liste d'ids."""
    order = _json_body(request).get("order") or []
    for idx, cid in enumerate(order):
        if str(cid).isdigit():
            Chapter.objects.filter(pk=int(cid), course_id=course_pk).update(position=idx)
    return _ok()


# ── Upload vidéo direct (navigateur -> Supabase, hors serveur) ────────────

def _storage_enabled() -> bool:
    return bool(os.environ.get("SUPABASE_S3_ACCESS_KEY") and os.environ.get("SUPABASE_S3_SECRET_KEY"))


def _s3_client_and_bucket(private: bool = False):
    """Client boto3 + bucket cible.

    private=True renvoie le bucket PRIVÉ (vidéos payantes, KYC, captures) — celui
    dont django-storages sert les fichiers via URL signée. Le presign PUT doit y
    déposer les fichiers pour que le presign GET (via .url) les retrouve.
    """
    import boto3
    from botocore.client import Config
    endpoint = os.environ.get("SUPABASE_S3_ENDPOINT") or (
        f"https://{os.environ.get('SUPABASE_PROJECT_REF', '')}.supabase.co/storage/v1/s3"
    )
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["SUPABASE_S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["SUPABASE_S3_SECRET_KEY"],
        region_name=os.environ.get("SUPABASE_S3_REGION", "us-west-2"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    if private:
        return client, os.environ.get("SUPABASE_PRIVATE_BUCKET", "private")
    return client, os.environ.get("SUPABASE_STORAGE_BUCKET", "media")


_ALLOWED_VIDEO_EXT = {"mp4", "webm", "mov", "m4v", "ogv", "ogg"}


@staff_required
@require_http_methods(["POST"])
def chapter_video_upload_url(request: HttpRequest, pk: int) -> JsonResponse:
    """Génère une URL présignée pour envoyer la vidéo DIRECTEMENT au stockage.

    Le fichier ne transite jamais par le serveur (contourne la limite Vercel).
    """
    if not Chapter.objects.filter(pk=pk).exists():
        return _error("Chapter not found", 404)
    if not _storage_enabled():
        return _error("Le stockage de fichiers n'est pas encore configuré.", 400)
    data = _json_body(request)
    filename = str(data.get("filename") or "video.mp4")
    content_type = str(data.get("content_type") or "").strip() or "video/mp4"
    if not content_type.startswith("video/"):
        return _error("Le fichier doit être une vidéo.", 400)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
    if ext not in _ALLOWED_VIDEO_EXT:
        return _error("Format vidéo non supporté (mp4, webm, mov…).", 400)
    key = f"courses/videos/chapter_{pk}.{ext}"
    client, bucket = _s3_client_and_bucket(private=True)
    url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=3600,
    )
    return JsonResponse({"url": url, "key": key, "content_type": content_type})


@staff_required
@require_http_methods(["POST"])
def chapter_video_confirm(request: HttpRequest, pk: int) -> JsonResponse:
    """Associe la vidéo (déjà envoyée au stockage) au chapitre."""
    try:
        ch = Chapter.objects.get(pk=pk)
    except Chapter.DoesNotExist:
        return _error("Chapter not found", 404)
    key = str(_json_body(request).get("key") or "").strip()
    # La cle doit correspondre a CE chapitre (evite de pointer la video d'un autre cours).
    if not key or not key.startswith(f"courses/videos/chapter_{pk}."):
        return _error("Clé de fichier invalide.", 400)
    old_name = ch.video.name if ch.video else ""
    ch.video.name = key
    ch.save(update_fields=["video"])
    # Efface l'ancienne vidéo si remplacée par un autre fichier (ex. format différent).
    # Utilise le storage du champ (bucket PRIVÉ), pas le storage public par défaut.
    if old_name and old_name != key:
        try:
            ch.video.storage.delete(old_name)
        except Exception:
            pass
    logger.info("Chapter %d video set by %s", pk, request.user.username)
    return JsonResponse(_serialize_chapter(ch))


@staff_required
@require_http_methods(["POST"])
def chapter_video_remove(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        ch = Chapter.objects.get(pk=pk)
    except Chapter.DoesNotExist:
        return _error("Chapter not found", 404)
    if ch.video:
        try:
            ch.video.delete(save=False)
        except Exception:
            pass
        ch.video = ""
        ch.save(update_fields=["video"])
    return JsonResponse(_serialize_chapter(ch))


# ── Plateforme de formation : utilisateurs & inscriptions (synchro admin) ──

def _serialize_profile(p: Profile) -> dict[str, Any]:
    u = p.user
    enroll = getattr(p, "enroll_count", None)
    if enroll is None:
        enroll = u.course_enrollments.count()
    return {
        "id": p.pk,
        "name": u.get_full_name() or u.username,
        "email": u.email,
        "role": p.role,
        "phone": p.phone,
        "is_approved": p.is_approved,
        "kyc_status": p.kyc_status,
        "kyc_status_label": p.get_kyc_status_display(),
        "id_number": p.id_number,
        "id_document": p.id_document.url if p.id_document else "",
        "kyc_note": p.kyc_note,
        "enrollments": enroll,
        "created_at": p.created_at.isoformat(),
    }


@staff_required
@require_http_methods(["POST"])
def learner_create(request: HttpRequest) -> JsonResponse:
    from django.contrib.auth.models import User
    data = _json_body(request)
    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    role = data.get("role") if data.get("role") in ("student", "teacher") else "student"
    if not name or not email:
        return _error("Le nom et l'email sont obligatoires.")
    if len(password) < 8:
        return _error("Le mot de passe doit contenir au moins 8 caractères.")
    if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
        return _error("Un compte existe déjà avec cet email.")
    parts = name.split(" ", 1)
    user = User.objects.create_user(
        username=email, email=email, password=password,
        first_name=parts[0], last_name=parts[1] if len(parts) > 1 else "",
    )
    p = Profile.objects.create(
        user=user, role=role, phone=str(data.get("phone") or ""),
        is_approved=(role == "student"),
        kyc_status=Profile.KycStatus.APPROVED if role == "student" else Profile.KycStatus.NOT_SUBMITTED,
    )
    logger.info("Profile created (%s) by %s", role, request.user.username)
    return JsonResponse(_serialize_profile(p), status=201)


@staff_required
def learner_list(request: HttpRequest) -> JsonResponse:
    qs = Profile.objects.select_related("user").annotate(
        enroll_count=Count("user__course_enrollments")
    ).all()
    role = request.GET.get("role")
    if role:
        qs = qs.filter(role=role)
    # Filtre file KYC (profs) : ?kyc_status=submitted|approved|rejected|not_submitted
    kyc = request.GET.get("kyc_status")
    if kyc in Profile.KycStatus.values:
        qs = qs.filter(kyc_status=kyc)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )
    return _paginated_response(qs.order_by("-created_at"), request, _serialize_profile)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def learner_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        p = Profile.objects.select_related("user").get(pk=pk)
    except Profile.DoesNotExist:
        return _error("Utilisateur introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_profile(p))
    if request.method == "PUT":
        data = _json_body(request)
        if "kyc_status" in data:
            status = data.get("kyc_status")
            if status in Profile.KycStatus.values:
                # Rejeter sans motif n'aide pas le professeur -> motif obligatoire.
                if status == Profile.KycStatus.REJECTED and not (
                    str(data.get("kyc_note") or "").strip() or p.kyc_note
                ):
                    return _error("Un motif de rejet est obligatoire.")
                p.kyc_status = status
                # Le statut KYC pilote l'approbation : « Vérifié » = accès débloqué.
                p.is_approved = (status == Profile.KycStatus.APPROVED)
        if "is_approved" in data and "kyc_status" not in data:
            p.is_approved = bool(data["is_approved"])
            if p.is_approved and p.kyc_status != Profile.KycStatus.APPROVED:
                p.kyc_status = Profile.KycStatus.APPROVED
        if "kyc_note" in data:
            p.kyc_note = str(data.get("kyc_note") or "")[:200]
        if "phone" in data:
            p.phone = str(data.get("phone") or "")[:40]
        # Edition du compte utilisateur (nom / email / reset mot de passe).
        u = p.user
        touched_user = False
        if "full_name" in data:
            name = str(data.get("full_name") or "").strip()
            parts = name.split()
            u.first_name = (parts[0] if parts else "")[:150]
            u.last_name = (" ".join(parts[1:]) if len(parts) > 1 else "")[:150]
            touched_user = True
        if "email" in data:
            email = str(data.get("email") or "").strip()
            if email and User.objects.filter(email=email).exclude(pk=u.pk).exists():
                return _error("Cet email est déjà utilisé par un autre compte.", 409)
            u.email = email[:254]
            touched_user = True
        if data.get("password"):
            u.set_password(data["password"])
            touched_user = True
        if touched_user:
            u.save()
        p.save()
        logger.info("Profile %d updated by %s", pk, request.user.username)
        return JsonResponse(_serialize_profile(p))
    user = p.user  # DELETE : supprime le compte (cascade profil + inscriptions)
    if user.is_superuser:
        return _error("Impossible de supprimer un super-administrateur.", 409)
    user.delete()
    return _ok()


@staff_required
def teacher_options(request: HttpRequest) -> JsonResponse:
    teachers = Profile.objects.filter(
        role=Profile.Role.TEACHER, is_approved=True
    ).select_related("user")
    return JsonResponse({
        "items": [
            {"id": p.user_id, "name": p.user.get_full_name() or p.user.username}
            for p in teachers
        ]
    })


@staff_required
def teacher_kyc_overview(request: HttpRequest) -> JsonResponse:
    """File de vérification KYC des professeurs : compteurs par statut + liste
    filtrable (?kyc_status/?search), les « à vérifier » (submitted) en premier."""
    from django.db.models import Case, IntegerField, When

    base = Profile.objects.filter(role=Profile.Role.TEACHER)
    raw = {row["kyc_status"]: row["n"] for row in base.values("kyc_status").annotate(n=Count("id"))}
    counts = {
        "all": sum(raw.values()),
        "submitted": raw.get(Profile.KycStatus.SUBMITTED, 0),
        "not_submitted": raw.get(Profile.KycStatus.NOT_SUBMITTED, 0),
        "rejected": raw.get(Profile.KycStatus.REJECTED, 0),
        "approved": raw.get(Profile.KycStatus.APPROVED, 0),
    }
    # annotate enroll_count : evite le N+1 de _serialize_profile (fallback .count()).
    qs = base.select_related("user").annotate(enroll_count=Count("user__course_enrollments"))
    status = request.GET.get("kyc_status")
    if status in Profile.KycStatus.values:
        qs = qs.filter(kyc_status=status)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )
    order = Case(
        When(kyc_status=Profile.KycStatus.SUBMITTED, then=0),
        When(kyc_status=Profile.KycStatus.NOT_SUBMITTED, then=1),
        When(kyc_status=Profile.KycStatus.REJECTED, then=2),
        When(kyc_status=Profile.KycStatus.APPROVED, then=3),
        default=4,
        output_field=IntegerField(),
    )
    qs = qs.annotate(_kyc_order=order).order_by("_kyc_order", "-created_at")
    items = [_serialize_profile(p) for p in qs[:300]]
    return JsonResponse({"counts": counts, "items": items})


def _serialize_course_enrollment(e: CourseEnrollment) -> dict[str, Any]:
    # Progression : chapitres terminés par l'étudiant / total du cours.
    # Utilise les annotations posées par course_enrollment_list quand elles
    # existent (évite le N+1) ; sinon (détail unitaire / PUT) on recalcule.
    total = getattr(e, "total_chapters", None)
    if total is None:
        total = e.course.chapters.count()
    done = getattr(e, "done_chapters", None)
    if done is None:
        done = ChapterCompletion.objects.filter(
            student_id=e.student_id, chapter__course_id=e.course_id
        ).count()
    return {
        "id": e.pk,
        "student_name": e.student.get_full_name() or e.student.username,
        "student_email": e.student.email,
        "course_title": e.course.title,
        "price_htg": e.course.price_htg,
        "status": e.status,
        "total_chapters": total,
        "done_chapters": min(done, total) if total else done,
        "created_at": e.created_at.isoformat(),
    }


@staff_required
def course_enrollment_list(request: HttpRequest) -> JsonResponse:
    from django.db.models import IntegerField, OuterRef, Subquery
    from django.db.models.functions import Coalesce

    # Sous-requêtes : nb de chapitres terminés (étudiant×cours) et total du cours.
    # Annotées pour éviter un N+1 sur la sérialisation de la liste.
    done_sq = (
        ChapterCompletion.objects
        .filter(student_id=OuterRef("student_id"), chapter__course_id=OuterRef("course_id"))
        .order_by().values("student_id").annotate(c=Count("id")).values("c")[:1]
    )
    total_sq = (
        Chapter.objects
        .filter(course_id=OuterRef("course_id"))
        .order_by().values("course_id").annotate(c=Count("id")).values("c")[:1]
    )
    qs = (
        CourseEnrollment.objects
        .select_related("student", "course")
        .annotate(
            done_chapters=Coalesce(Subquery(done_sq, output_field=IntegerField()), 0),
            total_chapters=Coalesce(Subquery(total_sq, output_field=IntegerField()), 0),
        )
    )
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(student__username__icontains=search) | Q(course__title__icontains=search))
    resp = _paginated_response(qs.order_by("-created_at"), request, _serialize_course_enrollment)

    # KPI globaux pour la vue pipeline : exacts (indépendants du filtre status
    # et de la pagination). Calculés seulement quand ?stats=1 -> pas de surcoût
    # pour l'usage tableau générique existant.
    if request.GET.get("stats"):
        stats = {"pending_count": 0, "active_count": 0, "pending_revenue": 0, "active_revenue": 0}
        agg = (
            CourseEnrollment.objects
            .values("status")
            .annotate(n=Count("id"), revenue=Sum("course__price_htg"))
        )
        for row in agg:
            if row["status"] == CourseEnrollment.Status.ACTIVE:
                stats["active_count"] = row["n"]
                stats["active_revenue"] = row["revenue"] or 0
            elif row["status"] == CourseEnrollment.Status.PENDING_PAYMENT:
                stats["pending_count"] = row["n"]
                stats["pending_revenue"] = row["revenue"] or 0
        payload = json.loads(resp.content)
        payload["stats"] = stats
        return JsonResponse(payload)
    return resp


def _materialize_course_payment(enrollment: CourseEnrollment) -> None:
    """Materialise UN Payment 'paye' quand une inscription formation devient
    ACTIVE et que le cours est payant, pour que le CA formation apparaisse dans
    la table Payment et le graphe des revenus (_serialize_revenue_for_react).

    Idempotent : au plus un Payment par CourseEnrollment, repere via
    external_reference = 'CE-<id>'. Ne fait RIEN si l'inscription n'est pas
    active ou si le cours est gratuit (price_htg == 0) -> aucun doublon ni
    revenu fantome. Ne touche jamais au Payment.enrollment (FK vers l'Enrollment
    core), laisse a None : ce paiement est rattache a la plateforme formation.
    """
    course = enrollment.course
    if enrollment.status != CourseEnrollment.Status.ACTIVE:
        return
    if not course or not course.price_htg:
        return
    ref = f"CE-{enrollment.pk}"
    student = enrollment.student
    payer_name = (student.get_full_name() or student.username or "Etudiant")[:140]
    try:
        # Anti-doublon ATOMIQUE : get_or_create (au lieu de exists()+create qui
        # laissait une fenetre TOCTOU -> deux CA 'CE-<id>' pour la meme inscription
        # = revenu formation double-compte). La cle external_reference sert d'ancre.
        Payment.objects.get_or_create(
            external_reference=ref,
            defaults={
                "purpose": Payment.Purpose.COURSE,
                "status": Payment.Status.PAID,
                "entry_mode": Payment.EntryMode.MANUAL,
                "payer_name": payer_name,
                "payer_email": getattr(student, "email", "") or "",
                "amount_htg": course.price_htg,
                "notes": f"Inscription formation · {course.title}",
            },
        )
    except Exception:
        # La materialisation du CA ne doit jamais casser l'activation d'un acces.
        logger.exception("Materialisation Payment formation echouee (CE=%s)", enrollment.pk)


def _cancel_course_payment(enrollment_pk: int) -> None:
    """Supprime le Payment materialise d'une inscription formation (external_
    reference='CE-<id>') quand elle quitte ACTIVE ou est supprimee. Evite de
    sur-compter le CA (inscription annulee comptee comme revenu)."""
    try:
        Payment.objects.filter(external_reference=f"CE-{enrollment_pk}").delete()
    except Exception:
        logger.exception("Annulation Payment formation echouee (CE=%s)", enrollment_pk)


@staff_required
@require_http_methods(["POST"])
def course_enrollment_create(request: HttpRequest) -> JsonResponse:
    """Inscription manuelle d'un etudiant a un cours par un admin (paiement recu
    hors-ligne, acces offert...). Recoit le pk du Profil etudiant + le pk du cours ;
    l'acces est actif par defaut (status=active) mais peut rester en attente."""
    data = _json_body(request)
    try:
        profile_id = int(data.get("student_id"))
        course_id = int(data.get("course_id"))
    except (TypeError, ValueError):
        return _error("Etudiant et cours obligatoires.")
    try:
        p = Profile.objects.select_related("user").get(pk=profile_id, role=Profile.Role.STUDENT)
    except Profile.DoesNotExist:
        return _error("Etudiant introuvable", 404)
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return _error("Cours introuvable", 404)
    status = data.get("status")
    if status not in (CourseEnrollment.Status.ACTIVE, CourseEnrollment.Status.PENDING_PAYMENT):
        status = CourseEnrollment.Status.ACTIVE
    e, created = CourseEnrollment.objects.get_or_create(
        student=p.user, course=course, defaults={"status": status},
    )
    if not created:
        return _error("Cet etudiant est deja inscrit a ce cours.", 409)
    logger.info(
        "CourseEnrollment created (student=%s course=%s status=%s) by %s",
        p.user_id, course_id, status, request.user.username,
    )
    # Cours payant deja active a la creation -> on materialise le revenu.
    _materialize_course_payment(e)
    return JsonResponse(_serialize_course_enrollment(e), status=201)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def course_enrollment_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        e = CourseEnrollment.objects.select_related("student", "course").get(pk=pk)
    except CourseEnrollment.DoesNotExist:
        return _error("Inscription introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_course_enrollment(e))
    if request.method == "PUT":
        st = _json_body(request).get("status")
        if st in (CourseEnrollment.Status.ACTIVE, CourseEnrollment.Status.PENDING_PAYMENT):
            e.status = st
            e.save(update_fields=["status", "updated_at"])
            logger.info("CourseEnrollment %d -> %s by %s", pk, st, request.user.username)
            if st == CourseEnrollment.Status.ACTIVE:
                # Passage a ACTIVE -> materialise le revenu (idempotent).
                _materialize_course_payment(e)
            else:
                # Quitte ACTIVE (repasse en attente) -> annule le CA materialise.
                _cancel_course_payment(e.pk)
        return JsonResponse(_serialize_course_enrollment(e))
    _cancel_course_payment(e.pk)  # suppression -> retirer le CA materialise
    e.delete()
    return _ok()


# ── Étudiants (formation) : segmentation d'accès + fiche détaillée ──

@staff_required
def student_overview(request: HttpRequest) -> JsonResponse:
    """Liste des étudiants segmentée par statut d'accès : compteurs globaux
    (tous / accès actif / paiement en attente) + items avec le nombre
    d'inscriptions actives et en attente par étudiant. Sert la barre de
    segmentation et la liste de la section « Étudiants »."""
    ACTIVE = CourseEnrollment.Status.ACTIVE
    PENDING = CourseEnrollment.Status.PENDING_PAYMENT
    base = Profile.objects.filter(role=Profile.Role.STUDENT)

    # Compteurs par segment (distinct : un étudiant a plusieurs inscriptions).
    counts = base.aggregate(
        all=Count("id", distinct=True),
        active=Count("id", filter=Q(user__course_enrollments__status=ACTIVE), distinct=True),
        pending=Count("id", filter=Q(user__course_enrollments__status=PENDING), distinct=True),
    )

    qs = base.select_related("user").annotate(
        enroll_count=Count("user__course_enrollments", distinct=True),
        active_count=Count("user__course_enrollments",
                           filter=Q(user__course_enrollments__status=ACTIVE), distinct=True),
        pending_count=Count("user__course_enrollments",
                            filter=Q(user__course_enrollments__status=PENDING), distinct=True),
    )
    # Filtre segment : on filtre sur l'annotation (HAVING) pour éviter la
    # duplication de lignes qu'entraînerait un filtre sur la jointure inverse.
    access = request.GET.get("access")
    if access == "active":
        qs = qs.filter(active_count__gt=0)
    elif access == "pending":
        qs = qs.filter(pending_count__gt=0)

    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    items = []
    for p in qs.order_by("-created_at")[:300]:
        row = _serialize_profile(p)
        row["active_count"] = getattr(p, "active_count", 0)
        row["pending_count"] = getattr(p, "pending_count", 0)
        items.append(row)
    return JsonResponse({"counts": counts, "items": items})


@staff_required
def student_detail(request: HttpRequest, pk: int) -> JsonResponse:
    """Fiche étudiant (drawer admin) : ses cours suivis avec, par cours, le
    statut de paiement (actif / paiement en attente) et la progression
    (chapitres terminés / total)."""
    try:
        p = Profile.objects.select_related("user").get(pk=pk, role=Profile.Role.STUDENT)
    except Profile.DoesNotExist:
        return _error("Étudiant introuvable", 404)

    user = p.user
    enrollments = list(
        CourseEnrollment.objects.filter(student=user)
        .select_related("course").order_by("-created_at")
    )
    course_ids = [e.course_id for e in enrollments]

    # Total de chapitres par cours + chapitres terminés par CET étudiant
    # (2 requêtes agrégées : pas de N+1).
    chap_totals = dict(
        Chapter.objects.filter(course_id__in=course_ids)
        .values("course_id").annotate(n=Count("id"))
        .values_list("course_id", "n")
    )
    done = dict(
        ChapterCompletion.objects.filter(student=user, chapter__course_id__in=course_ids)
        .values("chapter__course_id").annotate(n=Count("id"))
        .values_list("chapter__course_id", "n")
    )

    courses = []
    for e in enrollments:
        total = chap_totals.get(e.course_id, 0)
        completed = done.get(e.course_id, 0)
        pct = round(completed / total * 100) if total else 0
        courses.append({
            "enrollment_id": e.pk,
            "course_id": e.course_id,
            "course_title": e.course.title,
            "price_htg": e.course.price_htg,
            "status": e.status,
            "status_label": e.get_status_display(),
            "chapters_total": total,
            "chapters_done": completed,
            "progress": pct,
            "created_at": e.created_at.isoformat(),
        })

    data = _serialize_profile(p)
    active = sum(1 for e in enrollments if e.status == CourseEnrollment.Status.ACTIVE)
    data["active_count"] = active
    data["pending_count"] = len(enrollments) - active
    data["courses"] = courses
    return JsonResponse(data)


@staff_required
def student_export(request: HttpRequest) -> StreamingHttpResponse:
    """Export CSV de la liste des étudiants (respecte le segment ?access et la
    ?search courants). Colonnes lisibles (nom, email, tél, compteurs)."""
    ACTIVE = CourseEnrollment.Status.ACTIVE
    PENDING = CourseEnrollment.Status.PENDING_PAYMENT
    qs = Profile.objects.filter(role=Profile.Role.STUDENT).select_related("user").annotate(
        enroll_count=Count("user__course_enrollments", distinct=True),
        active_count=Count("user__course_enrollments",
                           filter=Q(user__course_enrollments__status=ACTIVE), distinct=True),
        pending_count=Count("user__course_enrollments",
                            filter=Q(user__course_enrollments__status=PENDING), distinct=True),
    )
    access = request.GET.get("access")
    if access == "active":
        qs = qs.filter(active_count__gt=0)
    elif access == "pending":
        qs = qs.filter(pending_count__gt=0)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )
    qs = qs.order_by("-created_at")
    header = ["Nom", "Email", "Téléphone", "Cours suivis",
              "Accès actifs", "Paiements en attente", "Inscrit le"]

    def _rows() -> Generator[str, None, None]:
        import csv, io
        yield "﻿"  # BOM UTF-8 (Excel FR)
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";")
        w.writerow(header)
        yield buf.getvalue(); buf.seek(0); buf.truncate(0)
        for p in qs.iterator():
            u = p.user
            w.writerow([
                _csv_safe(u.get_full_name() or u.username),
                _csv_safe(u.email or ""),
                _csv_safe(p.phone or ""),
                p.enroll_count, p.active_count, p.pending_count,
                p.created_at.strftime("%Y-%m-%d"),
            ])
            yield buf.getvalue(); buf.seek(0); buf.truncate(0)

    resp = StreamingHttpResponse(_rows(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="etudiants.csv"'
    return resp


# ── Bookings ─────────────────────────────────────────────

def _serialize_booking(b: VenueBooking) -> dict[str, Any]:
    payments = b.payments.all()
    return {
        "id": b.pk,
        "requester_name": b.requester_name,
        "requester_phone": b.requester_phone,
        "requester_email": b.requester_email,
        "event_type": b.event_type,
        "event_date": b.event_date.isoformat(),
        "start_time": b.start_time.isoformat(),
        "end_time": b.end_time.isoformat(),
        "guest_count": b.guest_count,
        "setup": b.setup,
        "status": b.status,
        "notes": b.notes,
        "payment_info": [
            {"id": p.pk, "reference": p.reference, "amount_htg": p.amount_htg,
             "status": p.status}
            for p in payments
        ],
        "created_at": b.created_at.isoformat(),
    }


@staff_required
def booking_list(request: HttpRequest) -> JsonResponse:
    from django.utils.dateparse import parse_date
    qs = VenueBooking.objects.prefetch_related("payments").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    date_from = _safe_date(request.GET.get("date_from"))
    if date_from:
        qs = qs.filter(event_date__gte=date_from)
    date_to = _safe_date(request.GET.get("date_to"))
    if date_to:
        qs = qs.filter(event_date__lte=date_to)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(requester_name__icontains=search) | Q(requester_phone__icontains=search)
            | Q(requester_email__icontains=search) | Q(event_type__icontains=search)
        )
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_booking)


@staff_required
@require_http_methods(["POST"])
def booking_create(request: HttpRequest) -> JsonResponse:
    """Réservation de salle saisie manuellement par un admin (demande hors-ligne).
    Contrôle anti double-réservation identique au flux public."""
    from django.utils.dateparse import parse_date, parse_time
    from apps.core.venue import slot_taken, OCCUPIED_STATUSES
    data = _json_body(request)
    name = str(data.get("requester_name") or "").strip()
    if not name:
        return _error("Le nom du demandeur est obligatoire.")
    # parse_date leve ValueError sur une date au bon format mais hors-plage
    # (ex. 2026-02-30) -> on rattrape pour renvoyer 400, pas 500.
    try:
        d = parse_date(str(data.get("event_date") or "")) if data.get("event_date") else None
    except ValueError:
        d = None
    if not d:
        return _error("La date de l'événement est invalide.")
    start = parse_time(str(data.get("start_time") or "")) or None
    end = parse_time(str(data.get("end_time") or "")) or None
    if not start or not end:
        return _error("Les heures de début et de fin sont obligatoires.")
    status = data.get("status") or VenueBooking.Status.REQUESTED
    if status not in VenueBooking.Status.values:
        return _error("Statut de réservation invalide.")
    if status in OCCUPIED_STATUSES and slot_taken(d, start, end):
        return _error("Ce créneau est déjà occupé par une autre réservation.", 409)
    try:
        guests = max(0, int(data.get("guest_count") or 0))
    except (ValueError, TypeError):
        guests = 0
    b = VenueBooking.objects.create(
        requester_name=name[:140],
        requester_phone=str(data.get("requester_phone") or "")[:40],
        requester_email=str(data.get("requester_email") or "")[:254],
        event_type=str(data.get("event_type") or "")[:80],
        event_date=d, start_time=start, end_time=end,
        guest_count=guests, setup=str(data.get("setup") or "")[:80],
        notes=str(data.get("notes") or ""), status=status,
    )
    logger.info("Booking %d created manually by %s", b.pk, request.user.username)
    return JsonResponse(_serialize_booking(b), status=201)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
def booking_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        b = VenueBooking.objects.prefetch_related("payments").get(pk=pk)
    except VenueBooking.DoesNotExist:
        return _error("Booking not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_booking(b))
    elif request.method == "PUT":
        data = _json_body(request)
        if "status" in data:
            if data["status"] not in VenueBooking.Status.values:
                return _error("Statut de réservation invalide.")
            b.status = data["status"]
        for fld in ("requester_name", "requester_phone", "requester_email",
                     "event_type", "setup", "notes"):
            if fld in data:
                setattr(b, fld, str(data[fld] or ""))
        # Champs date/heure requis : on refuse une valeur vide OU malformee (400)
        # au lieu de provoquer un 500 (chaîne invalide / contrainte NOT NULL).
        from django.utils.dateparse import parse_date, parse_time
        if "event_date" in data:
            try:
                d = parse_date(str(data["event_date"] or ""))
            except ValueError:
                d = None
            if not d:
                return _error("La date de l'événement est invalide.")
            b.event_date = d
        for fld, label in (("start_time", "L'heure de début"), ("end_time", "L'heure de fin")):
            if fld in data:
                try:
                    t = parse_time(str(data[fld] or ""))
                except ValueError:
                    t = None
                if not t:
                    return _error(f"{label} est invalide.")
                setattr(b, fld, t)
        if "guest_count" in data:
            try:
                b.guest_count = max(0, int(data["guest_count"] or 0))
            except (ValueError, TypeError):
                return _error("Le nombre d'invités doit être un nombre.")
        # Anti double-réservation : si ce créneau devient occupant (validé/confirmé
        # /en paiement) ou si l'horaire change, refuser s'il chevauche une AUTRE
        # réservation déjà occupante.
        from apps.core.venue import slot_taken, OCCUPIED_STATUSES
        if b.status in OCCUPIED_STATUSES and slot_taken(
            b.event_date, b.start_time, b.end_time, exclude_pk=b.pk
        ):
            return _error("Ce créneau est déjà occupé par une autre réservation.", 409)
        b.save()
        logger.info("Booking %d updated by user %s (status: %s)", pk, request.user.username, b.status)
        return JsonResponse(_serialize_booking(b))


# ── Payments ─────────────────────────────────────────────

def _serialize_payment(p: Payment) -> dict[str, Any]:
    return {
        "id": p.pk,
        "reference": p.reference,
        "purpose": p.purpose,
        "provider_id": p.provider_id,
        "provider_name": p.provider.name if p.provider else None,
        "status": p.status,
        "entry_mode": p.entry_mode,
        "payer_name": p.payer_name,
        "payer_phone": p.payer_phone,
        "payer_email": p.payer_email,
        "amount_htg": p.amount_htg,
        "external_reference": p.external_reference,
        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        "notes": p.notes,
        "venue_booking_id": p.venue_booking_id,
        "enrollment_id": p.enrollment_id,
        # Preuve de paiement (capture mobile money) : URL signée du bucket privé,
        # pour que l'admin valide sur pièce au lieu de basculer le statut à l'aveugle.
        "screenshot": p.screenshot.url if p.screenshot else "",
        "created_at": p.created_at.isoformat(),
    }


@staff_required
def payment_list(request: HttpRequest) -> JsonResponse:
    from django.utils.dateparse import parse_date
    qs = Payment.objects.select_related("provider").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    purpose = request.GET.get("purpose")
    if purpose:
        qs = qs.filter(purpose=purpose)
    # Dates : on ignore une valeur non parsable (evite un 500 sur filtre invalide).
    date_from = _safe_date(request.GET.get("date_from"))
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    date_to = _safe_date(request.GET.get("date_to"))
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(reference__icontains=search) | Q(payer_name__icontains=search)
            | Q(payer_phone__icontains=search) | Q(external_reference__icontains=search)
        )
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_payment)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
def payment_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        p = Payment.objects.select_related("provider").get(pk=pk)
    except Payment.DoesNotExist:
        return _error("Payment not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_payment(p))
    elif request.method == "PUT":
        data = _json_body(request)
        if "status" in data:
            if data["status"] not in Payment.Status.values:
                return _error("Statut de paiement invalide.")
            p.status = data["status"]
            # Renseigne/efface automatiquement la date de règlement.
            if p.status == Payment.Status.PAID and not p.paid_at:
                p.paid_at = timezone.now()
            elif p.status != Payment.Status.PAID:
                p.paid_at = None
        if "amount_htg" in data:
            try:
                amount = int(data["amount_htg"])
            except (ValueError, TypeError):
                return _error("Le montant doit être un nombre.")
            if amount < 0:
                return _error("Le montant ne peut pas être négatif.")
            p.amount_htg = amount
        if "purpose" in data:
            if data["purpose"] not in Payment.Purpose.values:
                return _error("Motif de paiement invalide.")
            p.purpose = data["purpose"]
        # Bornes de longueur : un save() nu n'applique PAS max_length et laisse
        # remonter une DataError Postgres -> 500. On tronque comme provider_detail.
        _pay_maxlen = {"payer_name": 140, "payer_phone": 40,
                        "payer_email": 254, "external_reference": 120, "entry_mode": 20}
        for fld in ("payer_name", "payer_phone", "payer_email",
                     "notes", "entry_mode", "external_reference"):
            if fld in data:
                val = str(data[fld] or "")
                if fld in _pay_maxlen:
                    val = val[: _pay_maxlen[fld]]
                setattr(p, fld, val)
        if "provider_id" in data:
            pid = data["provider_id"] or None
            if pid is not None:
                try:
                    pid = int(pid)
                except (ValueError, TypeError):
                    return _error("Moyen de paiement invalide.")
                if not PaymentProvider.objects.filter(pk=pid).exists():
                    return _error("Le moyen de paiement sélectionné n'existe pas.")
            p.provider_id = pid
        p.save()
        logger.info("Payment %d updated by user %s (status: %s)", pk, request.user.username, p.status)
        return JsonResponse(_serialize_payment(p))


@staff_required
@require_http_methods(["POST"])
def payment_create(request: HttpRequest) -> JsonResponse:
    """Enregistrement MANUEL d'un paiement : encaissement cash, mobile money
    hors-ligne, cotisation. entry_mode est force a 'manual'. Payment.save()
    genere la reference et renseigne paid_at si le statut est 'paid'."""
    data = _json_body(request)
    purpose = str(data.get("purpose") or "").strip()
    if purpose not in Payment.Purpose.values:
        return _error("Motif de paiement invalide.")
    payer_name = str(data.get("payer_name") or "").strip()
    if not payer_name:
        return _error("Le nom du payeur est obligatoire.")
    try:
        amount = int(data.get("amount_htg") or 0)
    except (ValueError, TypeError):
        return _error("Le montant doit être un nombre.")
    if amount < 0:
        return _error("Le montant ne peut pas être négatif.")
    status = data.get("status") or Payment.Status.PENDING
    if status not in Payment.Status.values:
        return _error("Statut de paiement invalide.")
    provider_id = data.get("provider_id") or None
    if provider_id is not None:
        try:
            provider_id = int(provider_id)
        except (ValueError, TypeError):
            return _error("Moyen de paiement invalide.")
        if not PaymentProvider.objects.filter(pk=provider_id).exists():
            return _error("Le moyen de paiement sélectionné n'existe pas.")
    # Bornes de longueur : un create() nu n'applique pas max_length -> 500 Postgres.
    p = Payment.objects.create(
        purpose=purpose,
        provider_id=provider_id,
        status=status,
        entry_mode=Payment.EntryMode.MANUAL,
        payer_name=payer_name[:140],
        payer_phone=str(data.get("payer_phone") or "")[:40],
        payer_email=str(data.get("payer_email") or "")[:254],
        amount_htg=amount,
        external_reference=str(data.get("external_reference") or "")[:120],
        notes=str(data.get("notes") or ""),
    )
    logger.info("Payment %d created manually by user %s (%s, %d HTG, %s)",
                p.pk, request.user.username, purpose, amount, status)
    return JsonResponse(_serialize_payment(p), status=201)


# ── Contacts ─────────────────────────────────────────────

def _serialize_contact(c: ContactRequest) -> dict[str, Any]:
    return {
        "id": c.pk,
        "full_name": c.full_name,
        "phone": c.phone,
        "email": c.email,
        "subject": c.subject,
        "message": c.message,
        "is_processed": c.is_processed,
        "created_at": c.created_at.isoformat(),
    }


@staff_required
def contact_list(request: HttpRequest) -> JsonResponse:
    qs = ContactRequest.objects.all()
    processed = request.GET.get("processed")
    if processed is not None and processed != "":
        qs = qs.filter(is_processed=processed.lower() in ("1", "true"))
    subject = request.GET.get("subject")
    if subject:
        qs = qs.filter(subject=subject)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(full_name__icontains=search) | Q(email__icontains=search)
            | Q(phone__icontains=search) | Q(subject__icontains=search)
            | Q(message__icontains=search)
        )
    resp = _paginated_response(qs.order_by("-created_at"), request, _serialize_contact)
    if request.GET.get("stats"):
        by_subject = {
            row["subject"]: row["n"]
            for row in ContactRequest.objects.values("subject").annotate(n=Count("id"))
        }
        payload = json.loads(resp.content)
        payload["stats"] = {
            "total": ContactRequest.objects.count(),
            "unprocessed": ContactRequest.objects.filter(is_processed=False).count(),
            "by_subject": by_subject,
        }
        return JsonResponse(payload)
    return resp


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def contact_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        c = ContactRequest.objects.get(pk=pk)
    except ContactRequest.DoesNotExist:
        return _error("Contact not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_contact(c))
    elif request.method == "PUT":
        data = _json_body(request)
        if "is_processed" in data:
            c.is_processed = bool(data["is_processed"])
        for fld in ("full_name", "phone", "email", "subject", "message"):
            if fld in data:
                setattr(c, fld, data[fld])
        c.save()
        logger.info("Contact %d updated by user %s (processed: %s)", pk, request.user.username, c.is_processed)
        return JsonResponse(_serialize_contact(c))
    # DELETE : nettoyage (spam / demande traitée).
    c.delete()
    logger.info("Contact %d deleted by user %s", pk, request.user.username)
    return _ok()


# ── GEIs ─────────────────────────────────────────────────

def _serialize_gei(g: GEI, member_count: int | None = None) -> dict[str, Any]:
    if member_count is None:
        member_count = getattr(g, 'member_count', g.members.count())
    return {
        "id": g.pk,
        "name": g.name,
        "city": g.city,
        "coordinator": g.coordinator,
        "is_active": g.is_active,
        "member_count": member_count,
        "created_at": g.created_at.isoformat(),
    }


def _filtered_geis(request: HttpRequest) -> QuerySet:
    qs = GEI.objects.annotate(member_count=Count("members")).all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(city__icontains=search))
    active = request.GET.get("active")
    if active in ("1", "0", "true", "false"):
        qs = qs.filter(is_active=active in ("1", "true"))
    sort_map = {
        "city": ("city", "name"),
        "name": ("name",),
        "members": ("-member_count",),
        "recent": ("-created_at",),
    }
    return qs.order_by(*sort_map.get(request.GET.get("sort"), ("city", "name")))


@staff_required
def gei_list(request: HttpRequest) -> JsonResponse:
    return _paginated_response(_filtered_geis(request), request, _serialize_gei)


@staff_required
def gei_overview(request: HttpRequest) -> JsonResponse:
    """Vue GEIs en un seul appel : liste paginée + stats globales."""
    qs = _filtered_geis(request)
    page, per_page, offset = _get_page_params(request)
    total = qs.count()
    items = [_serialize_gei(g) for g in qs[offset: offset + per_page]]
    all_geis = GEI.objects.all()
    return JsonResponse({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
        "stats": {
            "total": all_geis.count(),
            "active": all_geis.filter(is_active=True).count(),
            "inactive": all_geis.filter(is_active=False).count(),
            "members": Member.objects.filter(gei__isnull=False).count(),
        },
    })


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def gei_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        g = GEI.objects.get(pk=pk)
    except GEI.DoesNotExist:
        return _error("GEI not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_gei(g))
    elif request.method == "PUT":
        cleaned, err = _clean_gei_data(_json_body(request), partial=True)
        if err:
            return _error(err)
        for fld, val in cleaned.items():
            setattr(g, fld, val)
        g.save()
        logger.info("GEI %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_gei(g))
    elif request.method == "DELETE":
        # Suppression libre : les membres rattachés sont conservés (leur lien
        # vers le GEI passe à NULL). Aucune donnée détruite en cascade.
        logger.info("GEI %d deleted by user %s", pk, request.user.username)
        g.delete()
        return _ok()


_GEI_MAXLEN = {"name": 120, "city": 120, "coordinator": 120}
_GEI_LABELS = {"name": "Le nom", "city": "La ville"}


def _clean_gei_data(data: dict, *, partial: bool):
    """Valide/normalise un GEI. Retourne (cleaned, erreur). Empêche les 500."""
    cleaned: dict[str, Any] = {}
    for f in ("name", "city"):
        if f in data or not partial:
            val = str(data.get(f) or "").strip()
            if not val:
                return None, f"{_GEI_LABELS[f]} est obligatoire."
            if len(val) > _GEI_MAXLEN[f]:
                return None, f"{_GEI_LABELS[f]} ne peut pas dépasser {_GEI_MAXLEN[f]} caractères."
            cleaned[f] = val
    if "coordinator" in data or not partial:
        coord = str(data.get("coordinator") or "").strip()
        if len(coord) > _GEI_MAXLEN["coordinator"]:
            return None, "Le coordinateur ne peut pas dépasser 120 caractères."
        cleaned["coordinator"] = coord
    if "is_active" in data:
        cleaned["is_active"] = bool(data.get("is_active"))
    elif not partial:
        cleaned["is_active"] = True
    return cleaned, None


@staff_required
@require_http_methods(["POST"])
def gei_create(request: HttpRequest) -> JsonResponse:
    cleaned, err = _clean_gei_data(_json_body(request), partial=False)
    if err:
        return _error(err)
    g = GEI.objects.create(**cleaned)
    logger.info("GEI %d created by user %s (%s - %s)", g.pk, request.user.username, g.name, g.city)
    return JsonResponse(_serialize_gei(g), status=201)


# ── Providers ────────────────────────────────────────────

def _serialize_provider(p: PaymentProvider) -> dict[str, Any]:
    return {
        "id": p.pk,
        "name": p.name,
        "provider_type": p.provider_type,
        "mode": p.mode,
        "is_active": p.is_active,
        "logo": p.logo.url if p.logo else "",
        "instructions": p.instructions,
        "account_name": p.account_name,
        "account_number": p.account_number,
        "checkout_url": p.checkout_url,
        "api_public_key": p.api_public_key,
        "has_secret": bool(p.api_secret_key),  # jamais la valeur, juste sa présence
        "sort_order": p.sort_order,
        "created_at": p.created_at.isoformat(),
    }


@staff_required
def provider_list(request: HttpRequest) -> JsonResponse:
    qs = PaymentProvider.objects.all().order_by("sort_order", "name")
    return _paginated_response(qs, request, _serialize_provider)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def provider_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        p = PaymentProvider.objects.get(pk=pk)
    except PaymentProvider.DoesNotExist:
        return _error("Provider not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_provider(p))
    elif request.method == "PUT":
        data = _json_body(request)
        if data.get("provider_type") and data["provider_type"] not in PaymentProvider.ProviderType.values:
            return _error("Type de moyen de paiement invalide.")
        if data.get("mode") and data["mode"] not in PaymentProvider.Mode.values:
            return _error("Mode invalide.")
        if "sort_order" in data:
            try:
                data["sort_order"] = max(0, int(data.get("sort_order") or 0))
            except (ValueError, TypeError):
                return _error("L'ordre doit être un nombre.")
        # Bornes de longueur : un save() nu n'applique PAS max_length et laisse
        # remonter une DataError Postgres -> 500. On tronque comme provider_create.
        _maxlen = {
            "name": 120, "account_name": 120, "account_number": 80,
            "checkout_url": 200, "api_public_key": 255,
        }
        for fld in ("name", "provider_type", "mode", "is_active", "instructions",
                     "account_name", "account_number", "checkout_url",
                     "api_public_key", "sort_order"):
            if fld in data:
                val = data[fld]
                if fld == "is_active":
                    val = bool(val)
                elif fld in _maxlen and val is not None:
                    val = str(val)[: _maxlen[fld]]
                setattr(p, fld, val)
        # La clé secrète n'est mise à jour que si une nouvelle valeur est fournie
        # (un champ vide ne l'efface pas — évite de la perdre en éditant le reste).
        if data.get("api_secret_key"):
            p.api_secret_key = data["api_secret_key"]
        p.save()
        logger.info("Provider %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_provider(p))
    elif request.method == "DELETE":
        reason = _deletion_block_reason(p)
        if reason:
            return _error(reason, 409)
        logger.info("Provider %d deleted by user %s", pk, request.user.username)
        p.delete()
        return _ok()


@staff_required
@require_http_methods(["POST"])
def provider_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if not str(data.get("name") or "").strip():
        return _error("Le nom est obligatoire.")
    if data.get("provider_type") and data["provider_type"] not in PaymentProvider.ProviderType.values:
        return _error("Type de moyen de paiement invalide.")
    if data.get("mode") and data["mode"] not in PaymentProvider.Mode.values:
        return _error("Mode invalide.")
    try:
        data["sort_order"] = max(0, int(data.get("sort_order") or 0))
    except (ValueError, TypeError):
        return _error("L'ordre doit être un nombre.")
    p = PaymentProvider.objects.create(
        name=str(data["name"]).strip()[:120],
        provider_type=data.get("provider_type", PaymentProvider.ProviderType.MANUAL),
        mode=data.get("mode", PaymentProvider.Mode.MANUAL),
        is_active=data.get("is_active", True),
        instructions=data.get("instructions", ""),
        account_name=data.get("account_name", ""),
        account_number=data.get("account_number", ""),
        checkout_url=data.get("checkout_url", ""),
        api_public_key=data.get("api_public_key", ""),
        api_secret_key=data.get("api_secret_key", ""),
        sort_order=data.get("sort_order", 0),
    )
    logger.info("Provider %d created by user %s (%s)", p.pk, request.user.username, p.name)
    return JsonResponse(_serialize_provider(p), status=201)


@staff_required
def provider_overview(request: HttpRequest) -> JsonResponse:
    """Tous les moyens de paiement + stats (pour la vue premium)."""
    qs = PaymentProvider.objects.all().order_by("sort_order", "name")
    items = [_serialize_provider(p) for p in qs]
    return JsonResponse({
        "items": items,
        "stats": {
            "total": len(items),
            "active": sum(1 for i in items if i["is_active"]),
            "api": sum(1 for i in items if i["mode"] == "api"),
            "manual": sum(1 for i in items if i["mode"] == "manual"),
        },
    })


@staff_required
@require_http_methods(["POST"])
def provider_test_connection(request: HttpRequest, pk: int) -> JsonResponse:
    """Vérifie que les identifiants API d'un moyen de paiement sont valides.

    Implémenté pour Stripe (appel réel à l'API). Pour les autres fournisseurs,
    on vérifie seulement que les identifiants sont renseignés.
    """
    try:
        p = PaymentProvider.objects.get(pk=pk)
    except PaymentProvider.DoesNotExist:
        return _error("Provider not found", 404)
    secret = p.api_secret_key
    if not secret:
        return _error("Aucune clé secrète enregistrée pour ce moyen de paiement.", 400)
    if p.provider_type == PaymentProvider.ProviderType.STRIPE:
        try:
            import urllib.request
            import base64 as _b64
            req = urllib.request.Request("https://api.stripe.com/v1/balance")
            token = _b64.b64encode(f"{secret}:".encode()).decode()
            req.add_header("Authorization", f"Basic {token}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok = resp.status == 200
            return JsonResponse({"ok": ok, "message": "Connexion Stripe réussie ✓" if ok else "Réponse inattendue."})
        except urllib.error.HTTPError as e:
            return JsonResponse({"ok": False, "message": f"Clé Stripe invalide ({e.code})."}, status=200)
        except Exception:
            return JsonResponse({"ok": False, "message": "Impossible de joindre Stripe."}, status=200)
    return JsonResponse({"ok": True, "message": "Identifiants enregistrés. (Test en direct disponible pour Stripe ; MonCash/NatCash/PayPal seront validés lors d'un paiement réel.)"})


# ── Enrollments ──────────────────────────────────────────

def _serialize_enrollment(e: Enrollment) -> dict[str, Any]:
    return {
        "id": e.pk,
        "member": {
            "id": e.member.pk,
            "first_name": e.member.first_name,
            "last_name": e.member.last_name,
            "email": e.member.email,
            "phone": e.member.phone,
        } if e.member else None,
        "course": {
            "id": e.course.pk,
            "title": e.course.title,
            "category": e.course.category,
            "price_htg": e.course.price_htg,
        } if e.course else None,
        "status": e.status,
        "created_at": e.created_at.isoformat(),
    }


@staff_required
def enrollment_list(request: HttpRequest) -> JsonResponse:
    qs = Enrollment.objects.select_related("member", "course").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(member__first_name__icontains=search) | Q(member__last_name__icontains=search)
            | Q(member__phone__icontains=search) | Q(course__title__icontains=search)
        )
    resp = _paginated_response(qs.order_by("-created_at"), request, _serialize_enrollment)
    # KPI pipeline (exacts, indépendants du filtre/pagination) quand ?stats=1.
    if request.GET.get("stats"):
        agg = Enrollment.objects.values("status").annotate(n=Count("id"))
        by = {row["status"]: row["n"] for row in agg}
        # CA potentiel des inscriptions confirmées (prix des cours).
        confirmed_revenue = Enrollment.objects.filter(
            status=Enrollment.Status.CONFIRMED
        ).aggregate(t=Sum("course__price_htg"))["t"] or 0
        payload = json.loads(resp.content)
        payload["stats"] = {
            "total": sum(by.values()),
            "pending": by.get("pending", 0),
            "confirmed": by.get("confirmed", 0),
            "cancelled": by.get("cancelled", 0),
            "confirmed_revenue": confirmed_revenue,
        }
        return JsonResponse(payload)
    return resp


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
def enrollment_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        e = Enrollment.objects.select_related("member", "course").get(pk=pk)
    except Enrollment.DoesNotExist:
        return _error("Enrollment not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_enrollment(e))
    elif request.method == "PUT":
        data = _json_body(request)
        if "status" in data:
            if data["status"] not in Enrollment.Status.values:
                return _error("Statut d'inscription invalide.")
            e.status = data["status"]
        e.save()
        logger.info("Enrollment %d updated by user %s (status: %s)", pk, request.user.username, e.status)
        return JsonResponse(_serialize_enrollment(e))


# ── Summary ──────────────────────────────────────────────

@staff_required
def dashboard_summary(request: HttpRequest) -> JsonResponse:
    return JsonResponse(get_dashboard_summary(request))


# Par defaut (0), le resume est recalcule a chaque appel : synchronisation
# parfaite. On ne le met en cache que si un cache PARTAGE (Redis) est configure
# et que DASHBOARD_SUMMARY_CACHE_TTL > 0. Raison : sur Vercel, le cache par
# defaut (LocMemCache) est propre a chaque instance lambda -> compteurs figes et
# desynchronises pendant plusieurs minutes. Les comptages sont peu couteux.
def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    try:
        return int(raw) if str(raw).strip() else default
    except (TypeError, ValueError):
        return default


_SUMMARY_TTL = _env_int("DASHBOARD_SUMMARY_CACHE_TTL", 0)


def get_dashboard_summary(request: HttpRequest | None = None) -> dict[str, Any]:
    force_refresh = bool(request and request.GET.get("refresh"))
    if _SUMMARY_TTL and not force_refresh:
        cached = cache.get("dashboard_summary")
        if cached is not None:
            return cached
    savings = Member.objects.aggregate(total=Sum("monthly_saving_htg"))["total"] or 0
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_bookings = VenueBooking.objects.filter(created_at__gte=seven_days_ago).count()
    recent_payments_qs = Payment.objects.filter(created_at__gte=seven_days_ago)
    recent_payments_count = recent_payments_qs.count()
    # « Montant reçu (7j) » = argent RÉELLEMENT encaissé -> filtrer sur PAID
    # (cohérent avec total_revenue_htg ; sinon un paiement en attente/échoué
    # gonfle le CA affiché).
    recent_payments_sum = recent_payments_qs.filter(
        status=Payment.Status.PAID
    ).aggregate(total=Sum("amount_htg"))["total"] or 0
    result = {
        "active_members": Member.objects.filter(status=Member.Status.ACTIVE).count(),
        "active_gei": GEI.objects.filter(is_active=True).count(),
        "active_courses": Course.objects.filter(is_active=True).count(),
        "pending_contacts": ContactRequest.objects.filter(is_processed=False).count(),
        "pending_bookings": VenueBooking.objects.filter(status=VenueBooking.Status.REQUESTED).count(),
        "savings_htg": savings,
        "total_members": Member.objects.count(),
        "total_courses": Course.objects.count(),
        "total_revenue_htg": Payment.objects.filter(status=Payment.Status.PAID).aggregate(
            total=Sum("amount_htg")
        )["total"] or 0,
        "pending_enrollments": Enrollment.objects.filter(status=Enrollment.Status.PENDING).count(),
        # File de travail « À traiter » du tableau de bord (actions en attente).
        "pending_payments": Payment.objects.filter(status=Payment.Status.PENDING).count(),
        "bookings_to_review": VenueBooking.objects.filter(status=VenueBooking.Status.ADMIN_REVIEW).count(),
        "pending_formation": CourseEnrollment.objects.filter(status=CourseEnrollment.Status.PENDING_PAYMENT).count(),
        "recent_bookings": recent_bookings,
        "recent_payments_count": recent_payments_count,
        "recent_payments_sum": recent_payments_sum,
    }
    if _SUMMARY_TTL:
        cache.set("dashboard_summary", result, _SUMMARY_TTL)
    return result


@staff_required
def dashboard_charts(request: HttpRequest) -> JsonResponse:
    """Données pour les graphiques du tableau de bord (courbes + donuts)."""
    pay_status = list(Payment.objects.values("status").annotate(c=Count("id")))
    mem_status = list(Member.objects.values("status").annotate(c=Count("id")))
    cats = Course.objects.values("category").annotate(c=Count("id")).order_by("-c")
    # Top GEI par nombre de membres (widget « Top GEI par membres »).
    top_geis = list(
        GEI.objects.annotate(c=Count("members")).filter(c__gt=0)
        .order_by("-c").values("name", "c")[:6]
    )
    return JsonResponse({
        "revenue": _serialize_revenue_for_react(),
        "payments_by_status": [{"key": r["status"], "value": r["c"]} for r in pay_status],
        "members_by_status": [{"key": r["status"], "value": r["c"]} for r in mem_status],
        "categories": [{"name": r["category"] or "Autre", "value": r["c"]} for r in cats if r["category"]],
        "top_geis": [{"name": r["name"], "value": r["c"]} for r in top_geis],
    })


# ── Notifications ────────────────────────────────────────

def _serialize_notification(n: AdminNotification) -> dict[str, Any]:
    return {
        "id": n.pk,
        "message": n.message,
        "notification_type": n.notification_type,
        "related_id": n.related_id,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


@staff_required
def notification_list(request: HttpRequest) -> JsonResponse:
    qs = AdminNotification.objects.all()
    qs = qs.order_by("-is_read", "-created_at")[:20]
    return JsonResponse([_serialize_notification(n) for n in qs], safe=False)


@staff_required
def notification_check(request: HttpRequest) -> JsonResponse:
    since = request.GET.get("since")
    qs = AdminNotification.objects.all()
    if since:
        try:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since)
            if since_dt:
                if timezone.is_naive(since_dt):
                    since_dt = timezone.make_aware(since_dt)
                qs = qs.filter(created_at__gt=since_dt)
        except (ValueError, TypeError):
            pass
    qs = qs.order_by("-created_at")[:50]
    unread_count = AdminNotification.objects.filter(is_read=False).count()
    return JsonResponse({
        "notifications": [_serialize_notification(n) for n in qs],
        "unread_count": unread_count,
    })


@staff_required
@require_http_methods(["POST"])
def notification_read(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        n = AdminNotification.objects.get(pk=pk)
    except AdminNotification.DoesNotExist:
        return _error("Notification not found", 404)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return _ok()


@staff_required
@require_http_methods(["POST"])
def notification_read_all(request: HttpRequest) -> JsonResponse:
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    return _ok()


@staff_required
@require_http_methods(["POST", "DELETE"])
def notification_clear(request: HttpRequest) -> JsonResponse:
    """Efface (supprime) les notifications. ?scope=read supprime uniquement les
    notifications deja lues ; sinon TOUTES. « Marquer lu » ne fait que griser :
    ceci vide reellement le panneau."""
    qs = AdminNotification.objects.all()
    if request.GET.get("scope") == "read":
        qs = qs.filter(is_read=True)
    deleted, _ = qs.delete()
    logger.info("Notifications effacees (%s) par %s", request.GET.get("scope") or "toutes", request.user.username)
    return JsonResponse({"ok": True, "deleted": deleted})


# ── Testimonials (v1) ─────────────────────────────────────


def _serialize_testimonial(t: Testimonial) -> dict[str, Any]:
    return {
        "id": t.pk,
        "author_name": t.author_name,
        "author_initials": t.author_initials,
        "location": t.location,
        "text": t.text,
        "photo": t.photo.url if t.photo else "",
        "sort_order": t.sort_order,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat(),
    }


@staff_required
@require_http_methods(["GET"])
def testimonial_list(request: HttpRequest) -> JsonResponse:
    # Renvoie le format pagine standard {items,total,...} attendu par le dashboard
    # (auparavant une liste brute -> la section etait totalement cassee).
    qs = Testimonial.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(author_name__icontains=search) | Q(text__icontains=search) | Q(location__icontains=search)
        )
    return _paginated_response(qs.order_by("sort_order", "-created_at"), request, _serialize_testimonial)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def testimonial_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        t = Testimonial.objects.get(pk=pk)
    except Testimonial.DoesNotExist:
        return _error("Témoignage introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_testimonial(t))
    if request.method == "DELETE":
        t.delete()
        return _ok()
    data = _json_body(request)
    for field in ("author_name", "author_initials", "location", "text", "is_active"):
        if field in data:
            setattr(t, field, data[field])
    if "sort_order" in data:
        try:
            t.sort_order = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return _error("L'ordre doit être un nombre.")
    t.save()
    return JsonResponse(_serialize_testimonial(t))


@staff_required
@require_http_methods(["POST"])
def testimonial_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if not str(data.get("author_name") or "").strip():
        return _error("Le nom de l'auteur est obligatoire.")
    try:
        sort_order = max(0, int(data.get("sort_order") or 0))
    except (ValueError, TypeError):
        return _error("L'ordre doit être un nombre.")
    t = Testimonial.objects.create(
        author_name=str(data.get("author_name") or "").strip(),
        author_initials=data.get("author_initials", ""),
        location=data.get("location", ""),
        text=data.get("text", ""),
        sort_order=sort_order,
        is_active=data.get("is_active", True),
    )
    return JsonResponse(_serialize_testimonial(t), status=201)


# ── Valeurs & Processus (contenu du site vitrine) ─────
# CRUD calque sur les temoignages : le site vitrine boucle dessus avec un
# fallback ({% empty %}) sur le contenu code en dur tant qu'aucune ligne active
# n'est saisie.


def _serialize_core_value(v: CoreValue) -> dict[str, Any]:
    return {
        "id": v.pk,
        "title": v.title,
        "text": v.text,
        "icon": v.icon,
        "sort_order": v.sort_order,
        "is_active": v.is_active,
        "created_at": v.created_at.isoformat(),
    }


@staff_required
@require_http_methods(["GET"])
def core_value_list(request: HttpRequest) -> JsonResponse:
    qs = CoreValue.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(text__icontains=search))
    return _paginated_response(qs.order_by("sort_order", "id"), request, _serialize_core_value)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def core_value_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        v = CoreValue.objects.get(pk=pk)
    except CoreValue.DoesNotExist:
        return _error("Valeur introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_core_value(v))
    if request.method == "DELETE":
        v.delete()
        return _ok()
    data = _json_body(request)
    for field in ("title", "text", "icon", "is_active"):
        if field in data:
            setattr(v, field, data[field])
    if "sort_order" in data:
        try:
            v.sort_order = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return _error("L'ordre doit etre un nombre.")
    v.save()
    return JsonResponse(_serialize_core_value(v))


@staff_required
@require_http_methods(["POST"])
def core_value_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if not str(data.get("title") or "").strip():
        return _error("Le titre est obligatoire.")
    try:
        sort_order = max(0, int(data.get("sort_order") or 0))
    except (ValueError, TypeError):
        return _error("L'ordre doit etre un nombre.")
    v = CoreValue.objects.create(
        title=str(data.get("title") or "").strip(),
        text=data.get("text", ""),
        icon=str(data.get("icon") or "").strip(),
        sort_order=sort_order,
        is_active=data.get("is_active", True),
    )
    return JsonResponse(_serialize_core_value(v), status=201)


# ── Textes du site (registre editable) ───────────────────

def _serialize_sitetext(t: SiteText) -> dict[str, Any]:
    return {
        "id": t.pk,
        "key": t.key,
        "label": t.label,
        "group": t.group,
        "value": t.value,
        "sort_order": t.sort_order,
    }


@staff_required
@require_http_methods(["GET"])
def sitetext_list(request: HttpRequest) -> JsonResponse:
    qs = SiteText.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(label__icontains=search) | Q(key__icontains=search) | Q(group__icontains=search) | Q(value__icontains=search))
    group = request.GET.get("group")
    if group:
        qs = qs.filter(group=group)
    return _paginated_response(qs.order_by("group", "sort_order", "key"), request, _serialize_sitetext)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def sitetext_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        t = SiteText.objects.get(pk=pk)
    except SiteText.DoesNotExist:
        return _error("Texte introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_sitetext(t))
    if request.method == "DELETE":
        t.delete()
        return _ok()
    data = _json_body(request)
    # L'admin edite surtout `value` ; label/group ajustables aussi. La cle est
    # stable (referencee par les templates) -> modifiable seulement a la creation.
    if "value" in data:
        t.value = str(data.get("value") or "")
    if "label" in data:
        t.label = str(data.get("label") or "")[:200]
    if "group" in data:
        t.group = str(data.get("group") or "")[:60]
    if "sort_order" in data:
        try:
            t.sort_order = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return _error("L'ordre doit etre un nombre.")
    t.save()
    return JsonResponse(_serialize_sitetext(t))


@staff_required
@require_http_methods(["POST"])
def sitetext_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    key = str(data.get("key") or "").strip()
    if not key:
        return _error("La cle est obligatoire.")
    if SiteText.objects.filter(key=key).exists():
        return _error("Cette cle existe deja.", 409)
    t = SiteText.objects.create(
        key=key[:80],
        label=str(data.get("label") or key)[:200],
        group=str(data.get("group") or "")[:60],
        value=str(data.get("value") or ""),
        sort_order=max(0, int(data.get("sort_order") or 0)) if str(data.get("sort_order") or "0").isdigit() else 0,
    )
    return JsonResponse(_serialize_sitetext(t), status=201)


# ── Images du site (registre editable) ───────────────────

def _serialize_siteimage(t: SiteImage) -> dict[str, Any]:
    return {
        "id": t.pk,
        "key": t.key,
        "label": t.label,
        "group": t.group,
        "image": t.image.url if t.image else "",
        "alt": t.alt,
        "sort_order": t.sort_order,
    }


@staff_required
@require_http_methods(["GET"])
def siteimage_list(request: HttpRequest) -> JsonResponse:
    qs = SiteImage.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(label__icontains=search) | Q(key__icontains=search) | Q(group__icontains=search) | Q(alt__icontains=search))
    group = request.GET.get("group")
    if group:
        qs = qs.filter(group=group)
    return _paginated_response(qs.order_by("group", "sort_order", "key"), request, _serialize_siteimage)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def siteimage_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        t = SiteImage.objects.get(pk=pk)
    except SiteImage.DoesNotExist:
        return _error("Image introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_siteimage(t))
    if request.method == "DELETE":
        t.delete()
        return _ok()
    data = _json_body(request)
    # La cle est stable (referencee par les templates) -> non modifiable ici.
    # Le fichier image lui-meme transite par l'upload (api/upload/siteimage/<pk>/).
    if "label" in data:
        t.label = str(data.get("label") or "")[:200]
    if "group" in data:
        t.group = str(data.get("group") or "")[:60]
    if "alt" in data:
        t.alt = str(data.get("alt") or "")[:200]
    if "sort_order" in data:
        try:
            t.sort_order = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return _error("L'ordre doit etre un nombre.")
    t.save()
    return JsonResponse(_serialize_siteimage(t))


@staff_required
@require_http_methods(["POST"])
def siteimage_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    key = str(data.get("key") or "").strip()
    if not key:
        return _error("La cle est obligatoire.")
    if SiteImage.objects.filter(key=key).exists():
        return _error("Cette cle existe deja.", 409)
    t = SiteImage.objects.create(
        key=key[:80],
        label=str(data.get("label") or key)[:200],
        group=str(data.get("group") or "")[:60],
        alt=str(data.get("alt") or "")[:200],
        sort_order=max(0, int(data.get("sort_order") or 0)) if str(data.get("sort_order") or "0").isdigit() else 0,
    )
    return JsonResponse(_serialize_siteimage(t), status=201)


def _serialize_process_step(s: ProcessStep) -> dict[str, Any]:
    return {
        "id": s.pk,
        "title": s.title,
        "text": s.text,
        "meta": s.meta,
        "icon": s.icon,
        "image": s.image.url if s.image else "",
        "sort_order": s.sort_order,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat(),
    }


@staff_required
@require_http_methods(["GET"])
def process_step_list(request: HttpRequest) -> JsonResponse:
    qs = ProcessStep.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(text__icontains=search))
    return _paginated_response(qs.order_by("sort_order", "id"), request, _serialize_process_step)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def process_step_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        s = ProcessStep.objects.get(pk=pk)
    except ProcessStep.DoesNotExist:
        return _error("Etape introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_process_step(s))
    if request.method == "DELETE":
        s.delete()
        return _ok()
    data = _json_body(request)
    for field in ("title", "text", "meta", "icon", "is_active"):
        if field in data:
            setattr(s, field, data[field])
    if "sort_order" in data:
        try:
            s.sort_order = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return _error("L'ordre doit etre un nombre.")
    s.save()
    return JsonResponse(_serialize_process_step(s))


@staff_required
@require_http_methods(["POST"])
def process_step_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if not str(data.get("title") or "").strip():
        return _error("Le titre est obligatoire.")
    try:
        sort_order = max(0, int(data.get("sort_order") or 0))
    except (ValueError, TypeError):
        return _error("L'ordre doit etre un nombre.")
    s = ProcessStep.objects.create(
        title=str(data.get("title") or "").strip(),
        text=data.get("text", ""),
        meta=str(data.get("meta") or "").strip(),
        icon=str(data.get("icon") or "").strip()[:8],
        sort_order=sort_order,
        is_active=data.get("is_active", True),
    )
    return JsonResponse(_serialize_process_step(s), status=201)


# ── Products (boutique) ──────────────────────────────────

def _serialize_product(p: Product) -> dict[str, Any]:
    return {
        "id": p.pk,
        "name": p.name,
        "slug": p.slug,
        "kind": p.kind,
        "description": p.description,
        "price_htg": p.price_htg,
        "stock": p.stock,
        "is_active": p.is_active,
        "sort_order": p.sort_order,
        "image": p.image.url if p.image else "",
        "created_at": p.created_at.isoformat(),
    }


@staff_required
def product_list(request: HttpRequest) -> JsonResponse:
    qs = Product.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    active = (request.GET.get("active") or "").lower()
    # Ne filtrer QUE sur une valeur reconnue : sinon « ?active= » (vide) tombait
    # sur is_active=False et masquait TOUS les produits actifs.
    if active in ("1", "true"):
        qs = qs.filter(is_active=True)
    elif active in ("0", "false"):
        qs = qs.filter(is_active=False)
    qs = qs.order_by("sort_order", "name")
    return _paginated_response(qs, request, _serialize_product)


def _clean_product_data(data: dict, *, partial: bool):
    """Valide/normalise un produit (anti-500 : prix/stock, kind hors choix, nom)."""
    cleaned: dict[str, Any] = {}
    if "name" in data or not partial:
        name = str(data.get("name") or "").strip()
        if not name:
            return None, "Le nom du produit est obligatoire."
        if len(name) > 180:
            return None, "Le nom ne peut pas dépasser 180 caractères."
        cleaned["name"] = name
    if "kind" in data:
        if data.get("kind") not in Product.Kind.values:
            return None, "Type de produit invalide."
        cleaned["kind"] = data["kind"]
    elif not partial:
        cleaned["kind"] = Product.Kind.KIT
    for f, label in (("price_htg", "Le prix"), ("stock", "Le stock")):
        if f in data or not partial:
            raw = data.get(f)
            try:
                n = int(raw) if raw not in (None, "") else 0
            except (ValueError, TypeError):
                return None, f"{label} doit être un nombre."
            if n < 0:
                return None, f"{label} ne peut pas être négatif."
            cleaned[f] = n
    if "description" in data:
        cleaned["description"] = str(data.get("description") or "")
    elif not partial:
        cleaned["description"] = ""
    if "is_active" in data:
        cleaned["is_active"] = bool(data.get("is_active"))
    elif not partial:
        cleaned["is_active"] = True
    if "sort_order" in data:
        try:
            cleaned["sort_order"] = max(0, int(data.get("sort_order") or 0))
        except (ValueError, TypeError):
            return None, "L'ordre doit être un nombre."
    return cleaned, None


@staff_required
@require_http_methods(["POST"])
def product_create(request: HttpRequest) -> JsonResponse:
    cleaned, err = _clean_product_data(_json_body(request), partial=False)
    if err:
        return _error(err)
    p = Product.objects.create(**cleaned)
    logger.info("Product %d created by user %s (%s)", p.pk, request.user.username, p.name)
    return JsonResponse(_serialize_product(p), status=201)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def product_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        p = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return _error("Product not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_product(p))
    elif request.method == "PUT":
        cleaned, err = _clean_product_data(_json_body(request), partial=True)
        if err:
            return _error(err)
        for fld, val in cleaned.items():
            setattr(p, fld, val)
        p.save()
        logger.info("Product %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_product(p))
    elif request.method == "DELETE":
        if p.order_items.exists():
            return _error("Ce produit apparaît dans des commandes. Désactivez-le plutôt.", 409)
        logger.info("Product %d deleted by user %s", pk, request.user.username)
        p.delete()
        return _ok()


# ── Orders (commandes boutique) ──────────────────────────

def _serialize_order(o: Order) -> dict[str, Any]:
    return {
        "id": o.pk,
        "reference": o.reference,
        "customer_name": o.customer_name,
        "customer_phone": o.customer_phone,
        "customer_email": o.customer_email,
        "delivery_address": o.delivery_address,
        "city": o.city,
        "status": o.status,
        "total_htg": o.total_htg,
        "note": o.note,
        "items": [
            {
                "id": it.pk,
                "product_name": it.product_name,
                "quantity": it.quantity,
                "unit_price_htg": it.unit_price_htg,
            }
            for it in o.items.all()
        ],
        "created_at": o.created_at.isoformat(),
    }


@staff_required
def order_list(request: HttpRequest) -> JsonResponse:
    qs = Order.objects.prefetch_related("items").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(reference__icontains=search)
            | Q(customer_name__icontains=search)
            | Q(customer_phone__icontains=search)
        )
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_order)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
def order_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        o = Order.objects.prefetch_related("items").get(pk=pk)
    except Order.DoesNotExist:
        return _error("Order not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_order(o))
    data = _json_body(request)
    if "status" in data:
        if data["status"] not in Order.Status.values:
            return _error("Statut de commande invalide.")
        o.status = data["status"]
    for fld in ("note", "delivery_address", "city", "customer_name", "customer_phone", "customer_email"):
        if fld in data:
            setattr(o, fld, str(data[fld] or ""))
    o.save()
    logger.info("Order %d updated by user %s (status: %s)", pk, request.user.username, o.status)
    return JsonResponse(_serialize_order(o))


@staff_required
def order_payments(request: HttpRequest) -> JsonResponse:
    """Paiements liés à une commande (lecture seule) pour le drawer détail.
    N'expose PAS la capture (bucket privé) : uniquement les métadonnées."""
    try:
        pk = int(request.GET.get("order", 0))
    except (TypeError, ValueError):
        pk = 0
    try:
        o = Order.objects.prefetch_related("payments").get(pk=pk)
    except Order.DoesNotExist:
        return _error("Order not found", 404)
    items = [
        {
            "id": p.pk,
            "reference": p.reference,
            "status": p.status,
            "amount_htg": p.amount_htg,
            "entry_mode": p.entry_mode,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "created_at": p.created_at.isoformat(),
        }
        for p in o.payments.all()
    ]
    return JsonResponse({"items": items})


# ── Blog ─────────────────────────────────────────────────

def _serialize_blogpost(b: BlogPost) -> dict[str, Any]:
    return {
        "id": b.pk,
        "title": b.title,
        "slug": b.slug,
        "excerpt": b.excerpt,
        "body": b.body,
        "author": b.author,
        "status": b.status,
        "cover_image": b.cover_image.url if b.cover_image else "",
        "published_at": b.published_at.isoformat() if b.published_at else None,
        "scheduled_for": b.scheduled_for.isoformat() if b.scheduled_for else None,
        "created_at": b.created_at.isoformat(),
    }


@staff_required
def blog_list(request: HttpRequest) -> JsonResponse:
    qs = BlogPost.objects.all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(body__icontains=search) | Q(author__icontains=search))
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_blogpost)


def _blog_apply_status(b: BlogPost, status: str) -> None:
    """Cohérence des dates selon le statut (publié -> published_at auto)."""
    b.status = status
    if status == BlogPost.Status.PUBLISHED and not b.published_at:
        b.published_at = timezone.now()


def _parse_scheduled(raw):
    """Convertit la valeur datetime-local en datetime aware. (dt, erreur)."""
    from django.utils.dateparse import parse_datetime
    if not raw:
        return None, None
    dt = parse_datetime(str(raw))
    if dt is None:
        return None, "Date de programmation invalide."
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt, None


@staff_required
@require_http_methods(["POST"])
def blog_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    if not str(data.get("title") or "").strip():
        return _error("Le titre est obligatoire.")
    if not str(data.get("body") or "").strip():
        return _error("Le contenu est obligatoire.")
    status = data.get("status", BlogPost.Status.DRAFT)
    if status not in BlogPost.Status.values:
        return _error("Statut d'article invalide.")
    sched, err = _parse_scheduled(data.get("scheduled_for"))
    if err:
        return _error(err)
    if status == BlogPost.Status.SCHEDULED and not sched:
        return _error("Une date de programmation est requise pour un article programmé.")
    b = BlogPost.objects.create(
        title=data["title"],
        body=data["body"],
        excerpt=data.get("excerpt", ""),
        author=data.get("author", ""),
        scheduled_for=sched,
    )
    _blog_apply_status(b, status)
    b.save()
    logger.info("BlogPost %d created by user %s (%s)", b.pk, request.user.username, b.title)
    return JsonResponse(_serialize_blogpost(b), status=201)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def blog_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        b = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        return _error("Article introuvable", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_blogpost(b))
    elif request.method == "PUT":
        data = _json_body(request)
        if "status" in data and data["status"] not in BlogPost.Status.values:
            return _error("Statut d'article invalide.")
        for fld in ("title", "body", "excerpt", "author"):
            if fld in data:
                setattr(b, fld, str(data[fld] or ""))
        if "scheduled_for" in data:
            sched, err = _parse_scheduled(data.get("scheduled_for"))
            if err:
                return _error(err)
            b.scheduled_for = sched
        if "status" in data:
            if data["status"] == BlogPost.Status.SCHEDULED and not b.scheduled_for:
                return _error("Une date de programmation est requise pour un article programmé.")
            _blog_apply_status(b, data["status"])
        b.save()
        logger.info("BlogPost %d updated by user %s (status: %s)", pk, request.user.username, b.status)
        return JsonResponse(_serialize_blogpost(b))
    elif request.method == "DELETE":
        logger.info("BlogPost %d deleted by user %s", pk, request.user.username)
        b.delete()
        return _ok()


# ── Paramètres du site (singleton) ───────────────────────

SETTINGS_TEXT_FIELDS = [
    "site_name", "tagline", "contact_phone", "contact_whatsapp", "contact_email", "contact_address",
    "facebook_url", "instagram_url", "twitter_url", "linkedin_url", "youtube_url", "tiktok_url",
    "color_primary", "color_primary_dark", "color_accent", "color_highlight",
    "hero_title", "hero_subtitle", "hero_cta_text", "about_title", "about_text", "shop_intro", "footer_text",
    "stat_members", "stat_members_label", "stat_growth", "stat_growth_label",
    "stat_savings", "stat_savings_label", "stat_repayment", "stat_repayment_label",
    "stat_workshops", "stat_workshops_label", "stat_women", "stat_women_label",
    "formation_hero_title", "formation_hero_subtitle",
    "url_statuts", "url_calendrier", "url_rapport", "url_mentor", "url_presse", "url_mentions", "url_confidentialite",
    "meta_description", "meta_keywords",
]
SETTINGS_BOOL_FIELDS = ["show_shop", "show_blog", "show_courses", "show_testimonials", "maintenance_mode"]


def _serialize_settings(s: SiteSetting) -> dict[str, Any]:
    data = {f: getattr(s, f) for f in SETTINGS_TEXT_FIELDS + SETTINGS_BOOL_FIELDS}
    data["logo"] = s.logo.url if s.logo else ""
    data["updated_at"] = s.updated_at.isoformat()
    return data


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
def site_settings_detail(request: HttpRequest) -> JsonResponse:
    s = SiteSetting.load()
    if request.method == "GET":
        return JsonResponse(_serialize_settings(s))
    data = _json_body(request)
    for f in SETTINGS_TEXT_FIELDS:
        if f in data:
            val = str(data[f] or "").strip()
            # Normalise les URLs (réseaux sociaux, liens footer) : préfixe https://
            # si l'utilisateur a oublié le schéma, sinon le lien est cassé (relatif).
            if f.endswith("_url") and val and not val.startswith(("http://", "https://")):
                val = "https://" + val
            # Tronque à la max_length du champ : un save() nu n'applique PAS la
            # limite et laisse remonter une DataError Postgres -> 500 qui casse
            # TOUTE la sauvegarde des paramètres (comme sitetext/siteimage).
            try:
                max_len = s._meta.get_field(f).max_length
                if max_len:
                    val = val[:max_len]
            except Exception:
                pass
            setattr(s, f, val)
    for f in SETTINGS_BOOL_FIELDS:
        if f in data:
            setattr(s, f, bool(data[f]))
    s.save()
    logger.info("Site settings updated by user %s", request.user.username)
    return JsonResponse(_serialize_settings(s))


# ── Suppression en masse (« Tout supprimer » par section) ────────────────
# Opération DESTRUCTIVE et irréversible : réservée au super-administrateur et
# protégée par un jeton de confirmation ("SUPPRIMER"). L'url_name "bulk-delete"
# n'est mappé sur aucune section connue -> section_for_urlname renvoie
# "__unknown__" -> staff_required la refuse déjà à tout admin simple (fail-closed) ;
# on revérifie is_superuser ici par défense en profondeur.
_BULK_DELETE_MODELS = {
    "members": Member,
    "geis": GEI,
    "courses": Course,
    "payments": Payment,
    "bookings": VenueBooking,
    "enrollments": Enrollment,
    "contacts": ContactRequest,
    "products": Product,
    "orders": Order,
    "testimonials": Testimonial,
    "providers": PaymentProvider,
    "blog": BlogPost,
    "values": CoreValue,
    "steps": ProcessStep,
}


@staff_required
def bulk_delete_section(request: HttpRequest, section: str) -> JsonResponse:
    if request.method != "POST":
        return _error("Method not allowed", 405)
    if not getattr(request.user, "is_superuser", False):
        return _error("Réservé au super-administrateur.", 403)
    model = _BULK_DELETE_MODELS.get(section)
    if model is None:
        return _error("Section non prise en charge pour la suppression en masse.", 400)
    data = _json_body(request)
    if str(data.get("confirm") or "").strip().upper() != "SUPPRIMER":
        return _error("Confirmation invalide. Tapez SUPPRIMER pour confirmer.", 400)
    count = model.objects.count()
    # .delete() sur le QuerySet déclenche les signaux/cascade (nettoyage des
    # fichiers, annulation des paiements matérialisés, etc.) — comportement voulu.
    model.objects.all().delete()
    logger.warning(
        "BULK DELETE: %d ligne(s) de la section '%s' supprimées par le super-admin %s",
        count, section, request.user.username,
    )
    from .audit import log_action
    log_action("delete", section, "", section, f"Suppression EN MASSE de {count} enregistrement(s).")
    return JsonResponse({"ok": True, "deleted": count})


@staff_required
def bookings_reset(request: HttpRequest) -> JsonResponse:
    """Réinitialise le calendrier de réservation : annule TOUTES les réservations
    non déjà annulées -> toutes les dates redeviennent disponibles. L'historique
    est conservé (statut « Annulée »), contrairement à « Tout supprimer ».

    On utilise .update() (et non save() par ligne) pour NE PAS déclencher les
    signaux post_save (sinon une notification + un email « Réservation annulée »
    partiraient pour chaque réservation)."""
    if request.method != "POST":
        return _error("Method not allowed", 405)
    data = _json_body(request)
    if not data.get("confirm"):
        return _error("Confirmation requise.", 400)
    freed = (
        VenueBooking.objects.exclude(status=VenueBooking.Status.CANCELLED)
        .update(status=VenueBooking.Status.CANCELLED, updated_at=timezone.now())
    )
    logger.warning(
        "BOOKINGS RESET: %d réservation(s) annulées (dates libérées) par %s",
        freed, request.user.username,
    )
    from .audit import log_action
    log_action("update", "VenueBooking", "", "Calendrier", f"Réinitialisation : {freed} réservation(s) annulée(s).")
    return JsonResponse({"ok": True, "cancelled": freed})


@staff_required
def account_change_password(request: HttpRequest) -> JsonResponse:
    """Change le mot de passe du COMPTE CONNECTÉ (self-service). Accessible à tout
    membre du personnel pour SON propre compte (url_name dans ALWAYS_ALLOWED).
    Exige le mot de passe actuel + valide le nouveau via les validateurs Django
    (longueur mini, pas trop courant, pas 100% numérique) — impossible de remettre
    un mot de passe faible. La session reste active après le changement."""
    if request.method != "POST":
        return _error("Method not allowed", 405)
    data = _json_body(request)
    current = str(data.get("current_password") or "")
    new = str(data.get("new_password") or "")
    user = request.user
    if not user.check_password(current):
        return _error("Mot de passe actuel incorrect.", 400)
    if not new:
        return _error("Le nouveau mot de passe est vide.", 400)
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    try:
        validate_password(new, user=user)
    except ValidationError as exc:
        return _error(" ".join(exc.messages), 400)
    user.set_password(new)
    user.save(update_fields=["password"])
    update_session_auth_hash(request, user)  # évite la déconnexion immédiate
    logger.info("Mot de passe changé par l'utilisateur %s", user.username)
    from .audit import log_action
    log_action("update", "Admin", user.pk, user.get_username(), "Mot de passe changé (self-service).")
    return JsonResponse({"ok": True})


# ── Upload d'images ──────────────────────────────────────

_UPLOAD_TARGETS = {
    "product": (Product, "image"),
    "blog": (BlogPost, "cover_image"),
    "testimonial": (Testimonial, "photo"),
    "site": (SiteSetting, "logo"),
    "course": (Course, "banner"),
    "provider": (PaymentProvider, "logo"),
    "siteimage": (SiteImage, "image"),
    "processstep": (ProcessStep, "image"),
}
# Section RBAC associée à chaque cible d'upload (contrôle par section).
_UPLOAD_TARGET_SECTION = {
    "product": "products", "blog": "blog", "testimonial": "testimonials",
    "site": "settings", "course": "courses", "provider": "providers",
    "siteimage": "siteimages", "processstep": "steps",
}
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@staff_required
@require_http_methods(["POST"])
def upload_image(request: HttpRequest, target: str, pk: int) -> JsonResponse:
    if target not in _UPLOAD_TARGETS:
        return _error(f"Cible d'upload invalide: {target}", 404)
    # RBAC : un admin simple ne peut téléverser que dans ses sections autorisées
    # (sinon un admin « membres » pourrait remplacer le logo du site).
    from .sections import user_can
    if not user_can(request.user, _UPLOAD_TARGET_SECTION.get(target)):
        return _error("Vous n'avez pas accès à cette section.", 403)
    model_class, field = _UPLOAD_TARGETS[target]
    if target == "site":
        obj = SiteSetting.load()
    else:
        try:
            obj = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            return _error("Élément introuvable", 404)

    f = request.FILES.get("file")
    if not f:
        return _error("Aucun fichier fourni", 400)
    # Validation robuste par octets magiques + allowlist d'extension (refuse SVG
    # et fichiers déguisés) — ne pas se fier au content_type fourni par le client.
    from apps.core.upload_validation import validate_image_upload

    _err = validate_image_upload(f, max_bytes=_MAX_UPLOAD_BYTES)
    if _err:
        return _error(_err, 400)

    old = getattr(obj, field)
    old_name = old.name if old else ""
    setattr(obj, field, f)
    obj.save()
    # Efface l'ancienne image si elle a été remplacée (évite les orphelins).
    new_name = getattr(obj, field).name
    if old_name and old_name != new_name:
        try:
            default_storage.delete(old_name)
        except Exception:
            pass
    logger.info("Image uploaded (%s #%s, field %s) by user %s", target, getattr(obj, "pk", "-"), field, request.user.username)
    return JsonResponse({"ok": True, "url": getattr(obj, field).url})


# ── Administrateurs (comptes staff) ──────────────────────

def _serialize_admin(u) -> dict[str, Any]:
    sections: list[str] = []
    note = ""
    if not u.is_superuser:
        try:
            acc = u.admin_access
            sections = list(acc.sections or [])
            note = acc.note
        except Exception:
            sections = []
    return {
        "id": u.pk,
        "username": u.username,
        "email": u.email,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
        "is_active": u.is_active,
        "sections": sections,
        "note": note,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "date_joined": u.date_joined.isoformat(),
    }


def _require_superuser(request):
    if not request.user.is_superuser:
        return _error("Réservé aux super-administrateurs.", 403)
    return None


@staff_required
def admin_user_list(request: HttpRequest) -> JsonResponse:
    # select_related(admin_access) : _serialize_admin lit u.admin_access par ligne
    # -> sans ça, 1+N requetes sur la liste des administrateurs.
    qs = User.objects.filter(is_staff=True).select_related("admin_access").order_by("-is_superuser", "username")
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))
    return _paginated_response(qs, request, _serialize_admin)


@staff_required
@require_http_methods(["POST"])
def admin_user_create(request: HttpRequest) -> JsonResponse:
    denied = _require_superuser(request)
    if denied:
        return denied
    data = _json_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return _error("Nom d'utilisateur et mot de passe requis.")
    if User.objects.filter(username=username).exists():
        return _error("Ce nom d'utilisateur existe déjà.", 409)
    user = User.objects.create(
        username=username,
        email=(data.get("email") or "").strip(),
        is_staff=True,
        is_superuser=bool(data.get("is_superuser", False)),
        is_active=True,
    )
    user.set_password(password)
    user.save()
    # Sections attribuées (admins simples uniquement ; un super-admin a tout).
    if not user.is_superuser:
        from .sections import GRANTABLE_SECTIONS
        clean = [s for s in (data.get("sections") or []) if s in GRANTABLE_SECTIONS]
        AdminAccess.objects.create(user=user, sections=clean, note=(data.get("note") or "")[:200])
    logger.info("Admin user '%s' created by %s (superuser=%s, %d sections)",
                username, request.user.username, user.is_superuser, len(data.get("sections") or []))
    from .audit import log_action
    log_action("create", "Admin", user.pk, username,
               f"Nouvel administrateur — superuser={user.is_superuser}, sections={data.get('sections') or []}")
    return JsonResponse(_serialize_admin(user), status=201)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def admin_user_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return _error("Administrateur introuvable", 404)

    if request.method == "GET":
        return JsonResponse(_serialize_admin(user))

    denied = _require_superuser(request)
    if denied:
        return denied

    if request.method == "PUT":
        data = _json_body(request)
        if "email" in data:
            user.email = (data.get("email") or "").strip()
        if "is_active" in data:
            # Empêche de se désactiver soi-même
            if user.pk == request.user.pk and not data["is_active"]:
                return _error("Vous ne pouvez pas désactiver votre propre compte.", 400)
            user.is_active = bool(data["is_active"])
        if "is_superuser" in data:
            # Empêche de rétrograder le dernier super-administrateur (lockout).
            if user.is_superuser and not data["is_superuser"] and \
                    User.objects.filter(is_superuser=True, is_active=True).count() <= 1:
                return _error("Impossible de retirer le rôle au dernier super-administrateur.", 400)
            user.is_superuser = bool(data["is_superuser"])
        if data.get("password"):
            user.set_password(data["password"])
        user.is_staff = True
        user.save()
        # Sections attribuées / note de rôle (pour un admin simple).
        if "sections" in data or "note" in data:
            from .sections import GRANTABLE_SECTIONS
            acc, _ = AdminAccess.objects.get_or_create(user=user)
            if "sections" in data:
                acc.sections = [s for s in (data.get("sections") or []) if s in GRANTABLE_SECTIONS]
            if "note" in data:
                acc.note = (data.get("note") or "")[:200]
            acc.save()
        logger.info("Admin user '%s' updated by %s", user.username, request.user.username)
        from .audit import log_action
        _changed = [k for k in ("is_active", "is_superuser", "password", "sections", "note") if k in data]
        log_action("update", "Admin", user.pk, user.username,
                   "Compte admin modifié — champs : " + (", ".join(_changed) or "aucun"))
        return JsonResponse(_serialize_admin(user))

    if request.method == "DELETE":
        if user.pk == request.user.pk:
            return _error("Vous ne pouvez pas supprimer votre propre compte.", 400)
        if user.is_superuser and User.objects.filter(is_superuser=True).count() <= 1:
            return _error("Impossible de supprimer le dernier super-administrateur.", 400)
        logger.info("Admin user '%s' deleted by %s", user.username, request.user.username)
        from .audit import log_action
        log_action("delete", "Admin", user.pk, user.username,
                   f"Administrateur supprimé (superuser={user.is_superuser}).")
        user.delete()
        return _ok()


# ── Export CSV ───────────────────────────────────────────

ALLOWED_EXPORT_MODELS = {
    "members": Member,
    "courses": Course,
    "payments": Payment,
    "bookings": VenueBooking,
    "contacts": ContactRequest,
    "geis": GEI,
    "providers": PaymentProvider,
    "enrollments": Enrollment,
    "testimonials": Testimonial,
    "products": Product,
    "orders": Order,
    "blog": BlogPost,
}

# Champs jamais exportés (secrets fournisseurs de paiement, etc.).
SENSITIVE_EXPORT_FIELDS = {"api_secret_key", "api_public_key"}


def _export_fields(model_class) -> list[str]:
    """Champs exportables d'un modèle, en excluant les secrets et les champs
    chiffrés (dont la valeur serait déchiffrée par `getattr`)."""
    fields = []
    for f in model_class._meta.fields:
        if f.name in SENSITIVE_EXPORT_FIELDS:
            continue
        if isinstance(f, EncryptedCharField):
            continue
        # Pour une cle etrangere, exporter la colonne locale (attname, ex.
        # 'provider_id') au lieu du nom de relation : getattr(obj, 'provider')
        # chargerait l'objet lie -> 1 requete DB par FK et par ligne (N+1).
        fields.append(f.attname if f.is_relation else f.name)
    return fields


def _csv_safe(value: Any) -> Any:
    """Neutralise l'injection de formules CSV (Excel/Sheets).

    Une cellule commençant par = + - @ (ou tab/retour) peut etre interpretee
    comme une formule a l'ouverture. On la prefixe d'une apostrophe.
    """
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _csv_stream(queryset: QuerySet, fields: list[str]) -> Generator[str, None, None]:
    import csv, io
    # BOM UTF-8 + séparateur « ; » : le fichier s'ouvre proprement dans Excel FR
    # (accents corrects, colonnes séparées) et Google Sheets (détection auto).
    yield "﻿"
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(fields)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    for obj in queryset.iterator():
        writer.writerow([_csv_safe(getattr(obj, f, "")) for f in fields])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@staff_required
def export_csv(request: HttpRequest, model_name: str) -> HttpResponse:
    if model_name not in ALLOWED_EXPORT_MODELS:
        return _error(f"Modèle non autorisé: {model_name}", 404)
    # Croise la permission avec la SECTION du modèle exporté : un admin délégué à
    # qui l'on n'a donné que « export » ne doit pas pouvoir aspirer la PII de
    # sections qu'il ne détient pas (membres, paiements, contacts…). Les clés de
    # ALLOWED_EXPORT_MODELS coïncident avec les clés de section.
    if not request.user.is_superuser:
        from .sections import user_can

        if not user_can(request.user, model_name):
            return _error("Vous n'avez pas accès à l'export de ces données.", 403)
    model_class = ALLOWED_EXPORT_MODELS[model_name]
    qs = model_class.objects.all()
    _model_fields = {f.name for f in model_class._meta.fields}
    # Filtre période (réconciliation comptable) : event_date pour les réservations,
    # created_at sinon. Valeurs invalides ignorées (_safe_date).
    date_field = "event_date" if model_name == "bookings" else "created_at"
    if date_field in _model_fields:
        _lookup = f"{date_field}__gte" if date_field == "event_date" else f"{date_field}__date__gte"
        _lookup_to = f"{date_field}__lte" if date_field == "event_date" else f"{date_field}__date__lte"
        d_from = _safe_date(request.GET.get("date_from"))
        d_to = _safe_date(request.GET.get("date_to"))
        if d_from:
            qs = qs.filter(**{_lookup: d_from})
        if d_to:
            qs = qs.filter(**{_lookup_to: d_to})
    # Filtre statut (payments/orders/bookings/enrollments…) si le modèle en a un.
    status = request.GET.get("status")
    if status and "status" in _model_fields:
        qs = qs.filter(status=status)
    fields = _export_fields(model_class)
    response = StreamingHttpResponse(_csv_stream(qs, fields), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{model_name}.csv"'
    return response


# ── Journal d'audit (activité récente des administrateurs) ───────
def _serialize_audit_log(a: AuditLog) -> dict[str, Any]:
    return {
        "id": a.pk,
        "username": a.username or "—",
        "action": a.action,
        "action_label": a.get_action_display(),
        "model_name": a.model_name,
        "object_id": a.object_id,
        "object_label": a.object_label,
        "detail": a.detail,
        "created_at": a.created_at.isoformat(),
    }


@staff_required
def audit_log_list(request: HttpRequest) -> JsonResponse:
    """Timeline des actions du personnel (qui a créé/modifié/supprimé quoi)."""
    qs = AuditLog.objects.select_related("user")
    action = request.GET.get("action")
    if action in AuditLog.Action.values:
        qs = qs.filter(action=action)
    model_name = request.GET.get("model")
    if model_name:
        qs = qs.filter(model_name=model_name)
    return _paginated_response(qs.order_by("-created_at"), request, _serialize_audit_log)

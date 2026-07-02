from __future__ import annotations

import csv
import json
import logging
from datetime import timedelta
from typing import Any, Callable, Generator

from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count, Sum, Q
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

from .permissions import StaffRequiredMixin, staff_required
from .models import (
    AdminNotification,
    ContactRequest,
    Course,
    EncryptedCharField,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    Testimonial,
    VenueBooking,
)


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="post")
@method_decorator(ratelimit(key="post:username", rate="5/m", method="POST", block=True), name="post")
class RateLimitedLoginView(LoginView):
    """Login admin avec limitation anti-force-brute (par IP et par identifiant)."""

    template_name = "adminpanel/login.html"
    redirect_authenticated_user = True


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = "adminpanel/simple_dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["summary"] = get_dashboard_summary()
        context["django_version"] = "5.2.15"
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
    qs = Payment.objects.select_related("provider", "enrollment__member", "enrollment__course").all()[:20]
    result = []
    for p in qs:
        member_name = p.payer_name
        course_title = ""
        if p.enrollment and p.enrollment.course:
            course_title = p.enrollment.course.title
        elif p.purpose == "venue" and p.venue_booking:
            course_title = f"Réservation: {p.venue_booking.event_type}"

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
    months = []
    for i in range(6):
        dt = now - timedelta(days=30 * (5 - i))
        months.append(dt)

    result = []
    for dt in months:
        total = Payment.objects.filter(
            status=Payment.Status.PAID,
            created_at__year=dt.year,
            created_at__month=dt.month,
        ).aggregate(total=Sum("amount_htg"))["total"] or 0
        result.append({
            "m": _month_abbr(dt),
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
    per_page = min(per_page, 100)
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
        return json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return {}


def _error(msg: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": msg}, status=status)


def _ok() -> JsonResponse:
    return JsonResponse({"ok": True})


def _deletion_block_reason(instance: Any) -> str | None:
    """Retourne un message si la suppression est dangereuse (données liées), sinon None.

    Évite les suppressions destructrices : un membre supprimé efface en cascade
    ses inscriptions ; un GEI/cours/fournisseur supprimé casse des liens. On
    conseille plutôt de désactiver (statut) que de supprimer.
    """
    if isinstance(instance, Member):
        if instance.enrollments.exists():
            return "Ce membre possède des inscriptions. Passez son statut à « Ancien » plutôt que de le supprimer."
    elif isinstance(instance, GEI):
        if instance.members.exists():
            return "Des membres sont rattachés à ce GEI. Désactivez-le plutôt que de le supprimer."
    elif isinstance(instance, Course):
        if instance.enrollments.exists():
            return "Ce cours a des inscriptions. Désactivez-le plutôt que de le supprimer."
    elif isinstance(instance, PaymentProvider):
        if instance.payments.exists():
            return "Ce fournisseur est lié à des paiements. Désactivez-le plutôt que de le supprimer."
    return None


@staff_required
@require_http_methods(["POST"])
def member_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    for f in ("first_name", "last_name", "phone"):
        if f not in data:
            return _error(f"Missing field: {f}")
    m = Member.objects.create(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data.get("email", ""),
        phone=data["phone"],
        gei_id=data.get("gei_id") or data.get("gei"),
        status=data.get("status", Member.Status.PROSPECT),
        joined_at=data.get("joined_at"),
        monthly_saving_htg=data.get("monthly_saving_htg", 0),
    )
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
        "gei__name": gei.name if gei else None,
        "gei__city": gei.city if gei else None,
        "status": m.status,
        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        "monthly_saving_htg": m.monthly_saving_htg,
        "created_at": m.created_at.isoformat(),
    }


@staff_required
def member_list(request: HttpRequest) -> JsonResponse:
    qs = Member.objects.select_related("gei").all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )
    gei = request.GET.get("gei")
    if gei:
        qs = qs.filter(gei_id=gei)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_member)


@staff_required
def member_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        m = Member.objects.select_related("gei").get(pk=pk)
    except Member.DoesNotExist:
        return _error("Member not found", 404)
    if request.method == "GET":
        return JsonResponse(_serialize_member(m))
    elif request.method == "PUT":
        data = _json_body(request)
        for field in ("first_name", "last_name", "email", "phone", "status", "joined_at", "monthly_saving_htg"):
            if field in data:
                setattr(m, field, data[field])
        if "gei_id" in data:
            m.gei_id = data["gei_id"]
        elif "gei" in data:
            m.gei_id = data["gei"]
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


# ── Courses ──────────────────────────────────────────────

def _serialize_course(c: Course, enroll_count: int | None = None) -> dict[str, Any]:
    if enroll_count is None:
        enroll_count = getattr(c, 'enrollment_count', c.enrollments.count())
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
        "enrollment_count": enroll_count,
        "created_at": c.created_at.isoformat(),
    }


@staff_required
def course_list(request: HttpRequest) -> JsonResponse:
    qs = Course.objects.annotate(enrollment_count=Count("enrollments")).all()
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
    if active is not None:
        qs = qs.filter(is_active=active.lower() in ("1", "true"))
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_course)


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
        data = _json_body(request)
        for fld in ("title", "category", "instructor", "city", "price_htg",
                     "capacity", "is_active", "public_slug", "description"):
            if fld in data:
                setattr(c, fld, data[fld])
        c.save()
        logger.info("Course %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_course(c))
    elif request.method == "DELETE":
        reason = _deletion_block_reason(c)
        if reason:
            return _error(reason, 409)
        logger.info("Course %d deleted by user %s", pk, request.user.username)
        c.delete()
        return _ok()


@staff_required
@require_http_methods(["POST"])
def course_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    required = ("title", "category", "instructor", "city", "price_htg", "capacity")
    for f in required:
        if f not in data:
            return _error(f"Missing field: {f}")
    c = Course.objects.create(
        title=data["title"],
        category=data["category"],
        instructor=data["instructor"],
        city=data.get("city", ""),
        price_htg=data.get("price_htg", 0),
        capacity=data.get("capacity", 0),
        is_active=data.get("is_active", True),
        public_slug=data.get("public_slug", ""),
        description=data.get("description", ""),
    )
    logger.info("Course %d created by user %s (%s)", c.pk, request.user.username, c.title)
    return JsonResponse(_serialize_course(c), status=201)


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
    qs = VenueBooking.objects.prefetch_related("payments").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(event_date__gte=date_from)
    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(event_date__lte=date_to)
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_booking)


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
            b.status = data["status"]
        for fld in ("requester_name", "requester_phone", "requester_email",
                     "event_type", "event_date", "start_time", "end_time",
                     "guest_count", "setup", "notes"):
            if fld in data:
                setattr(b, fld, data[fld])
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
        "created_at": p.created_at.isoformat(),
    }


@staff_required
def payment_list(request: HttpRequest) -> JsonResponse:
    qs = Payment.objects.select_related("provider").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    purpose = request.GET.get("purpose")
    if purpose:
        qs = qs.filter(purpose=purpose)
    date_from = request.GET.get("date_from")
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    date_to = request.GET.get("date_to")
    if date_to:
        qs = qs.filter(created_at__lte=date_to)
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
            p.status = data["status"]
        for fld in ("payer_name", "payer_phone", "payer_email", "amount_htg",
                     "notes", "entry_mode", "external_reference"):
            if fld in data:
                setattr(p, fld, data[fld])
        if "provider_id" in data:
            p.provider_id = data["provider_id"]
        p.save()
        logger.info("Payment %d updated by user %s (status: %s)", pk, request.user.username, p.status)
        return JsonResponse(_serialize_payment(p))


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
    if processed is not None:
        qs = qs.filter(is_processed=processed.lower() in ("1", "true"))
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_contact)


@ensure_csrf_cookie
@staff_required
@require_http_methods(["GET", "PUT"])
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


@staff_required
def gei_list(request: HttpRequest) -> JsonResponse:
    qs = GEI.objects.annotate(member_count=Count("members")).all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(city__icontains=search))
    active = request.GET.get("active")
    if active is not None:
        qs = qs.filter(is_active=active.lower() in ("1", "true"))
    qs = qs.order_by("city", "name")
    return _paginated_response(qs, request, _serialize_gei)


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
        data = _json_body(request)
        for fld in ("name", "city", "coordinator", "is_active"):
            if fld in data:
                setattr(g, fld, data[fld])
        g.save()
        logger.info("GEI %d updated by user %s", pk, request.user.username)
        return JsonResponse(_serialize_gei(g))
    elif request.method == "DELETE":
        reason = _deletion_block_reason(g)
        if reason:
            return _error(reason, 409)
        logger.info("GEI %d deleted by user %s", pk, request.user.username)
        g.delete()
        return _ok()


@staff_required
@require_http_methods(["POST"])
def gei_create(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    for f in ("name", "city"):
        if f not in data:
            return _error(f"Missing field: {f}")
    g = GEI.objects.create(
        name=data["name"],
        city=data["city"],
        coordinator=data.get("coordinator", ""),
        is_active=data.get("is_active", True),
    )
    logger.info("GEI %d created by user %s (%s - %s)", g.pk, request.user.username, g.name, g.city)
    return JsonResponse(_serialize_gei(g), status=201)


# ── Providers ────────────────────────────────────────────

def _serialize_provider(p: PaymentProvider) -> dict[str, Any]:
    return {
        "id": p.pk,
        "name": p.name,
        "provider_type": p.provider_type,
        "is_active": p.is_active,
        "instructions": p.instructions,
        "checkout_url": p.checkout_url,
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
        for fld in ("name", "provider_type", "is_active", "instructions",
                     "checkout_url", "api_public_key", "sort_order"):
            if fld in data:
                setattr(p, fld, data[fld])
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
    if "name" not in data:
        return _error("Missing field: name")
    p = PaymentProvider.objects.create(
        name=data["name"],
        provider_type=data.get("provider_type", PaymentProvider.ProviderType.MANUAL),
        is_active=data.get("is_active", True),
        instructions=data.get("instructions", ""),
        checkout_url=data.get("checkout_url", ""),
        api_public_key=data.get("api_public_key", ""),
        sort_order=data.get("sort_order", 0),
    )
    logger.info("Provider %d created by user %s (%s)", p.pk, request.user.username, p.name)
    return JsonResponse(_serialize_provider(p), status=201)


# ── Enrollments ──────────────────────────────────────────

def _serialize_enrollment(e: Enrollment) -> dict[str, Any]:
    return {
        "id": e.pk,
        "member": {
            "id": e.member.pk,
            "first_name": e.member.first_name,
            "last_name": e.member.last_name,
            "email": e.member.email,
        } if e.member else None,
        "course": {
            "id": e.course.pk,
            "title": e.course.title,
            "category": e.course.category,
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
    qs = qs.order_by("-created_at")
    return _paginated_response(qs, request, _serialize_enrollment)


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
            e.status = data["status"]
        e.save()
        logger.info("Enrollment %d updated by user %s (status: %s)", pk, request.user.username, e.status)
        return JsonResponse(_serialize_enrollment(e))


# ── Summary ──────────────────────────────────────────────

@staff_required
def dashboard_summary(request: HttpRequest) -> JsonResponse:
    return JsonResponse(get_dashboard_summary(request))


def get_dashboard_summary(request: HttpRequest | None = None) -> dict[str, Any]:
    if request and request.GET.get("refresh"):
        cache.delete("dashboard_summary")
    cached = cache.get("dashboard_summary")
    if cached is not None:
        return cached
    savings = Member.objects.aggregate(total=Sum("monthly_saving_htg"))["total"] or 0
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_bookings = VenueBooking.objects.filter(created_at__gte=seven_days_ago).count()
    recent_payments_qs = Payment.objects.filter(created_at__gte=seven_days_ago)
    recent_payments_count = recent_payments_qs.count()
    recent_payments_sum = recent_payments_qs.aggregate(total=Sum("amount_htg"))["total"] or 0
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
        "recent_bookings": recent_bookings,
        "recent_payments_count": recent_payments_count,
        "recent_payments_sum": recent_payments_sum,
    }
    cache.set("dashboard_summary", result, 300)
    return result


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


# ── Testimonials (v1) ─────────────────────────────────────


@staff_required
@require_http_methods(["GET"])
def testimonial_list(request: HttpRequest) -> JsonResponse:
    qs = Testimonial.objects.all()
    data = [
        {
            "id": t.pk,
            "author_name": t.author_name,
            "author_initials": t.author_initials,
            "location": t.location,
            "text": t.text,
            "sort_order": t.sort_order,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in qs
    ]
    return JsonResponse(data, safe=False)


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def testimonial_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        t = Testimonial.objects.get(pk=pk)
    except Testimonial.DoesNotExist:
        return _error("Témoignage introuvable", 404)

    if request.method == "GET":
        return JsonResponse({
            "id": t.pk,
            "author_name": t.author_name,
            "author_initials": t.author_initials,
            "location": t.location,
            "text": t.text,
            "photo": t.photo.url if t.photo else "",
            "sort_order": t.sort_order,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        })

    if request.method == "DELETE":
        t.delete()
        return _ok()

    data = json.loads(request.body.decode("utf-8"))
    for field in ("author_name", "location", "text", "sort_order", "is_active"):
        if field in data:
            setattr(t, field, data[field])
    t.save()
    return _ok()


@staff_required
@require_http_methods(["POST"])
def testimonial_create(request: HttpRequest) -> JsonResponse:
    data = json.loads(request.body.decode("utf-8"))
    t = Testimonial.objects.create(
        author_name=data.get("author_name", ""),
        author_initials=data.get("author_initials", ""),
        location=data.get("location", ""),
        text=data.get("text", ""),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True),
    )
    return JsonResponse({"ok": True, "id": t.pk}, status=201)


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
        fields.append(f.name)
    return fields


def _csv_stream(queryset: QuerySet, fields: list[str]) -> Generator[str, None, None]:
    import csv, io
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(fields)
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    for obj in queryset.iterator():
        writer.writerow([getattr(obj, f, "") for f in fields])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@staff_required
def export_csv(request: HttpRequest, model_name: str) -> HttpResponse:
    if model_name not in ALLOWED_EXPORT_MODELS:
        return _error(f"Modèle non autorisé: {model_name}", 404)
    model_class = ALLOWED_EXPORT_MODELS[model_name]
    qs = model_class.objects.all()
    fields = _export_fields(model_class)
    response = StreamingHttpResponse(_csv_stream(qs, fields), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{model_name}.csv"'
    return response

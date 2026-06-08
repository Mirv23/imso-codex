import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .models import (
    AdminNotification,
    ContactRequest,
    Course,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    VenueBooking,
)


@method_decorator(login_required(login_url="/django-admin/login/"), name="dispatch")
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "adminpanel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = get_dashboard_summary()
        return context


def _get_page_params(request):
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


def _paginated_response(queryset, request, serializer):
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


def _json_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return {}


def _error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def _ok():
    return JsonResponse({"ok": True})


# ── Members ──────────────────────────────────────────────

def _serialize_member(m):
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


@login_required(login_url="/django-admin/login/")
def member_list(request):
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
    return JsonResponse([_serialize_member(m) for m in qs], safe=False)


@login_required(login_url="/django-admin/login/")
def member_detail(request, pk):
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
        return JsonResponse(_serialize_member(m))
    elif request.method == "DELETE":
        m.delete()
        return _ok()
    return _error("Method not allowed", 405)


# ── Courses ──────────────────────────────────────────────

def _serialize_course(c, enroll_count=None):
    if enroll_count is None:
        enroll_count = c.enrollments.count()
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


@login_required(login_url="/django-admin/login/")
def course_list(request):
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
    return JsonResponse([
        {
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
            "enrollment_count": c.enrollment_count,
            "created_at": c.created_at.isoformat(),
        }
        for c in qs
    ], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT", "DELETE"])
def course_detail(request, pk):
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
        return JsonResponse(_serialize_course(c))
    elif request.method == "DELETE":
        c.delete()
        return _ok()


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["POST"])
def course_create(request):
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
    return JsonResponse(_serialize_course(c), status=201)


# ── Bookings ─────────────────────────────────────────────

def _serialize_booking(b):
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


@login_required(login_url="/django-admin/login/")
def booking_list(request):
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
    return JsonResponse([_serialize_booking(b) for b in qs], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT"])
def booking_detail(request, pk):
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
        return JsonResponse(_serialize_booking(b))


# ── Payments ─────────────────────────────────────────────

def _serialize_payment(p):
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


@login_required(login_url="/django-admin/login/")
def payment_list(request):
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
    return JsonResponse([_serialize_payment(p) for p in qs], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT"])
def payment_detail(request, pk):
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
        return JsonResponse(_serialize_payment(p))


# ── Contacts ─────────────────────────────────────────────

def _serialize_contact(c):
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


@login_required(login_url="/django-admin/login/")
def contact_list(request):
    qs = ContactRequest.objects.all()
    processed = request.GET.get("processed")
    if processed is not None:
        qs = qs.filter(is_processed=processed.lower() in ("1", "true"))
    qs = qs.order_by("-created_at")
    return JsonResponse([_serialize_contact(c) for c in qs], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT"])
def contact_detail(request, pk):
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
        return JsonResponse(_serialize_contact(c))


# ── GEIs ─────────────────────────────────────────────────

def _serialize_gei(g, member_count=None):
    if member_count is None:
        member_count = g.members.count()
    return {
        "id": g.pk,
        "name": g.name,
        "city": g.city,
        "coordinator": g.coordinator,
        "is_active": g.is_active,
        "member_count": member_count,
        "created_at": g.created_at.isoformat(),
    }


@login_required(login_url="/django-admin/login/")
def gei_list(request):
    qs = GEI.objects.annotate(member_count=Count("members")).all()
    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(city__icontains=search))
    active = request.GET.get("active")
    if active is not None:
        qs = qs.filter(is_active=active.lower() in ("1", "true"))
    qs = qs.order_by("city", "name")
    return JsonResponse([
        {
            "id": g.pk,
            "name": g.name,
            "city": g.city,
            "coordinator": g.coordinator,
            "is_active": g.is_active,
            "member_count": g.member_count,
            "created_at": g.created_at.isoformat(),
        }
        for g in qs
    ], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT", "DELETE"])
def gei_detail(request, pk):
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
        return JsonResponse(_serialize_gei(g))
    elif request.method == "DELETE":
        g.delete()
        return _ok()


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["POST"])
def gei_create(request):
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
    return JsonResponse(_serialize_gei(g), status=201)


# ── Providers ────────────────────────────────────────────

def _serialize_provider(p):
    return {
        "id": p.pk,
        "name": p.name,
        "provider_type": p.provider_type,
        "is_active": p.is_active,
        "instructions": p.instructions,
        "checkout_url": p.checkout_url,
        "api_public_key": p.api_public_key,
        "sort_order": p.sort_order,
        "created_at": p.created_at.isoformat(),
    }


@login_required(login_url="/django-admin/login/")
def provider_list(request):
    qs = PaymentProvider.objects.all().order_by("sort_order", "name")
    return JsonResponse([_serialize_provider(p) for p in qs], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT", "DELETE"])
def provider_detail(request, pk):
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
        return JsonResponse(_serialize_provider(p))
    elif request.method == "DELETE":
        p.delete()
        return _ok()


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["POST"])
def provider_create(request):
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
    return JsonResponse(_serialize_provider(p), status=201)


# ── Enrollments ──────────────────────────────────────────

def _serialize_enrollment(e):
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


@login_required(login_url="/django-admin/login/")
def enrollment_list(request):
    qs = Enrollment.objects.select_related("member", "course").all()
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")
    return JsonResponse([_serialize_enrollment(e) for e in qs], safe=False)


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["GET", "PUT"])
def enrollment_detail(request, pk):
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
        return JsonResponse(_serialize_enrollment(e))


# ── Summary ──────────────────────────────────────────────

@login_required(login_url="/django-admin/login/")
def dashboard_summary(request):
    return JsonResponse(get_dashboard_summary())


def get_dashboard_summary():
    savings = Member.objects.aggregate(total=Sum("monthly_saving_htg"))["total"] or 0
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_bookings = VenueBooking.objects.filter(created_at__gte=seven_days_ago).count()
    recent_payments_qs = Payment.objects.filter(created_at__gte=seven_days_ago)
    recent_payments_count = recent_payments_qs.count()
    recent_payments_sum = recent_payments_qs.aggregate(total=Sum("amount_htg"))["total"] or 0
    return {
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


# ── Notifications ────────────────────────────────────────

def _serialize_notification(n):
    return {
        "id": n.pk,
        "message": n.message,
        "notification_type": n.notification_type,
        "related_id": n.related_id,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


@login_required(login_url="/django-admin/login/")
def notification_list(request):
    qs = AdminNotification.objects.all()
    qs = qs.order_by("-is_read", "-created_at")[:20]
    return JsonResponse([_serialize_notification(n) for n in qs], safe=False)


@login_required(login_url="/django-admin/login/")
def notification_check(request):
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


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["POST"])
def notification_read(request, pk):
    try:
        n = AdminNotification.objects.get(pk=pk)
    except AdminNotification.DoesNotExist:
        return _error("Notification not found", 404)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return _ok()


@csrf_exempt
@login_required(login_url="/django-admin/login/")
@require_http_methods(["POST"])
def notification_read_all(request):
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    return _ok()

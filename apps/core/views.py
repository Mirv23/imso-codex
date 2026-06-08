import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.adminpanel.models import (
    Course,
    Enrollment,
    Member,
    Payment,
    PaymentProvider,
    VenueBooking,
)
from .forms import ContactRequestForm, CourseEnrollmentRequestForm, VenueBookingRequestForm


class HomeView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_courses"] = Course.objects.filter(is_active=True)
        context["active_providers"] = PaymentProvider.objects.filter(is_active=True)
        return context


def healthcheck(_request):
    return JsonResponse({"status": "ok", "service": "imso"})


class ContactRequestCreateView(View):
    def post(self, request):
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = ContactRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        contact = form.save()
        return JsonResponse({"ok": True, "id": contact.id}, status=201)


class VenueBookingCreateView(View):
    def post(self, request):
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = VenueBookingRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        booking = form.save()
        return JsonResponse({
            "ok": True,
            "id": booking.id,
            "payment_url": f"/paiement/reservation/{booking.id}/",
        }, status=201)


class CourseEnrollmentCreateView(View):
    def post(self, request):
        payload = request.POST
        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except json.JSONDecodeError:
                return JsonResponse({"ok": False, "errors": {"body": ["JSON invalide"]}}, status=400)

        form = CourseEnrollmentRequestForm(payload)
        if not form.is_valid():
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)

        member = form.get_or_create_member()
        course_id = form.cleaned_data.get("course_id")
        course_title = form.cleaned_data.get("course_title")
        course_price = form.cleaned_data.get("course_price_htg", 0)

        course = None
        if course_id:
            course = get_object_or_404(Course, id=course_id)

        enrollment = Enrollment.objects.create(
            member=member,
            course=course,
            status=Enrollment.Status.PENDING,
        )

        return JsonResponse({
            "ok": True,
            "id": enrollment.id,
            "payment_url": f"/paiement/cours/{enrollment.id}/",
        }, status=201)


from django.core.serializers.json import DjangoJSONEncoder


class PaymentPageView(TemplateView):
    template_name = "core/paiement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        providers = PaymentProvider.objects.filter(is_active=True)
        context["providers"] = providers
        context["providers_json"] = json.dumps(list(providers.values(
            "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
        )), cls=DjangoJSONEncoder)

        payment_type = kwargs.get("type")
        payment_id = kwargs.get("id")

        context["payment_purpose"] = "other"
        context["payment_label"] = "Paiement"
        context["amount_htg"] = 0
        context["payer_name"] = ""
        context["payer_phone"] = ""
        context["payer_email"] = ""
        context["booking_id"] = None
        context["enrollment_id"] = None

        if payment_type == "reservation":
            booking = get_object_or_404(VenueBooking, id=payment_id)
            context["booking"] = booking
            context["payment_purpose"] = "venue"
            context["payment_label"] = f"Réservation de salle - {booking.event_type}"
            context["amount_htg"] = 0
            context["payer_name"] = booking.requester_name
            context["payer_phone"] = booking.requester_phone
            context["payer_email"] = booking.requester_email
            context["booking_id"] = booking.id
        elif payment_type == "cours":
            enrollment = get_object_or_404(Enrollment, id=payment_id)
            context["enrollment"] = enrollment
            context["payment_purpose"] = "course"
            context["payment_label"] = f"Inscription - {enrollment.course.title if enrollment.course else 'Cours'}"
            context["amount_htg"] = enrollment.course.price_htg if enrollment.course else 0
            context["payer_name"] = enrollment.member.get_full_name() or enrollment.member.first_name
            context["payer_phone"] = enrollment.member.phone
            context["payer_email"] = enrollment.member.email
            context["enrollment_id"] = enrollment.id

        return context


class PaymentProcessView(View):
    def post(self, request, type, id):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "JSON invalide"}, status=400)

        provider_id = data.get("provider_id")
        if not provider_id:
            return JsonResponse({"ok": False, "error": "Mode de paiement requis"}, status=400)

        provider = get_object_or_404(PaymentProvider, id=provider_id, is_active=True)

        booking = None
        enrollment = None
        purpose = Payment.Purpose.OTHER
        amount = 0
        payer_name = data.get("payer_name", "")
        payer_phone = data.get("payer_phone", "")
        payer_email = data.get("payer_email", "")

        if type == "reservation":
            booking = get_object_or_404(VenueBooking, id=id)
            purpose = Payment.Purpose.VENUE
            payer_name = payer_name or booking.requester_name
            payer_phone = payer_phone or booking.requester_phone
            payer_email = payer_email or booking.requester_email
            if booking.status == VenueBooking.Status.REQUESTED:
                booking.status = VenueBooking.Status.PAYMENT_PENDING
                booking.save(update_fields=["status", "updated_at"])
        elif type == "cours":
            enrollment = get_object_or_404(Enrollment, id=id)
            purpose = Payment.Purpose.COURSE
            amount = enrollment.course.price_htg if enrollment.course else 0
            payer_name = payer_name or enrollment.member.get_full_name() or enrollment.member.first_name
            payer_phone = payer_phone or enrollment.member.phone
            payer_email = payer_email or enrollment.member.email

        payment = Payment.objects.create(
            purpose=purpose,
            provider=provider,
            status=Payment.Status.PENDING,
            entry_mode=Payment.EntryMode.CLIENT,
            payer_name=payer_name,
            payer_phone=payer_phone,
            payer_email=payer_email,
            amount_htg=amount,
            venue_booking=booking,
            enrollment=enrollment,
            notes=f"Paiement initié via {provider.name}",
        )

        if provider.checkout_url:
            return JsonResponse({
                "ok": True,
                "payment_id": payment.id,
                "reference": payment.reference,
                "redirect_url": provider.checkout_url,
            })

        return JsonResponse({
            "ok": True,
            "payment_id": payment.id,
            "reference": payment.reference,
            "message": "Paiement enregistré. En attente de validation.",
            "instructions": provider.instructions,
        })


class PaymentConfirmationView(View):
    def get(self, request, reference):
        payment = get_object_or_404(Payment, reference=reference)
        return JsonResponse({
            "ok": True,
            "reference": payment.reference,
            "status": payment.status,
            "purpose": payment.purpose,
            "amount_htg": payment.amount_htg,
            "paid_at": payment.paid_at,
        })


def get_active_providers(request):
    providers = PaymentProvider.objects.filter(is_active=True).values(
        "id", "name", "provider_type", "instructions", "checkout_url", "sort_order"
    )
    return JsonResponse(list(providers), safe=False)


def get_active_courses(request):
    courses = Course.objects.filter(is_active=True).values(
        "id", "title", "category", "city", "instructor", "price_htg", "capacity", "description", "public_slug"
    )
    return JsonResponse(list(courses), safe=False)

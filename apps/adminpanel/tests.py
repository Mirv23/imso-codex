import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

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


# ── GEI ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestGEIModel:
    def test_creation(self):
        gei = GEI.objects.create(name="Test GEI", city="Port-au-Prince")
        assert gei.pk is not None
        assert gei.name == "Test GEI"
        assert gei.city == "Port-au-Prince"

    def test_str(self):
        gei = GEI.objects.create(name="Cap GEI", city="Cap-Haïtien")
        assert str(gei) == "Cap GEI - Cap-Haïtien"

    def test_is_active_default(self):
        gei = GEI.objects.create(name="Jacmel GEI", city="Jacmel")
        assert gei.is_active is True


# ── Member ───────────────────────────────────────────────

@pytest.mark.django_db
class TestMemberModel:
    def test_creation(self):
        gei = GEI.objects.create(name="GEI", city="Ville")
        member = Member.objects.create(
            first_name="Jean",
            last_name="Dupont",
            phone="+50912345678",
            gei=gei,
        )
        assert member.pk is not None

    def test_status_choices_default(self):
        member = Member.objects.create(
            first_name="Marie",
            last_name="Pierre",
            phone="+50987654321",
        )
        assert member.status == Member.Status.PROSPECT

    def test_status_choices_active(self):
        member = Member.objects.create(
            first_name="Paul",
            last_name="Saint",
            phone="+50911111111",
            status=Member.Status.ACTIVE,
        )
        assert member.status == "active"

    def test_str(self):
        member = Member.objects.create(
            first_name="Alice",
            last_name="Midi",
            phone="+50922222222",
        )
        assert str(member) == "Alice Midi"


# ── Course ───────────────────────────────────────────────

@pytest.mark.django_db
class TestCourseModel:
    def test_creation(self):
        course = Course.objects.create(
            title="Python Avancé",
            category="Programmation",
            instructor="M. Jean",
            city="Port-au-Prince",
            price_htg=5000,
            capacity=20,
        )
        assert course.pk is not None

    def test_str(self):
        course = Course.objects.create(
            title="Introduction à Django",
            category="Programmation",
            instructor="Mme Anne",
            city="Cap-Haïtien",
        )
        assert str(course) == "Introduction à Django"


# ── Enrollment ───────────────────────────────────────────

@pytest.mark.django_db
class TestEnrollmentModel:
    def test_creation(self):
        gei = GEI.objects.create(name="GEI", city="Ville")
        member = Member.objects.create(first_name="Test", last_name="User", phone="+50900000000", gei=gei)
        course = Course.objects.create(title="Cours Test", category="Test", instructor="Prof", city="Ville")
        enrollment = Enrollment.objects.create(member=member, course=course)
        assert enrollment.pk is not None
        assert enrollment.status == Enrollment.Status.PENDING

    def test_unique_together(self):
        gei = GEI.objects.create(name="GEI", city="Ville")
        member = Member.objects.create(first_name="A", last_name="B", phone="+50900000001", gei=gei)
        course = Course.objects.create(title="Cours Unique", category="Test", instructor="Prof", city="Ville")
        Enrollment.objects.create(member=member, course=course)
        with pytest.raises(Exception):
            Enrollment.objects.create(member=member, course=course)

    def test_str(self):
        gei = GEI.objects.create(name="GEI", city="Ville")
        member = Member.objects.create(first_name="Test", last_name="User", phone="+50900000002", gei=gei)
        course = Course.objects.create(title="Cours Str", category="Test", instructor="Prof", city="Ville")
        enrollment = Enrollment.objects.create(member=member, course=course)
        assert str(enrollment) == "Test User - Cours Str"


# ── VenueBooking ─────────────────────────────────────────

@pytest.mark.django_db
class TestVenueBookingModel:
    def test_creation(self):
        from datetime import date, time
        booking = VenueBooking.objects.create(
            requester_name="John Doe",
            requester_phone="+50933333333",
            event_type="Conférence",
            event_date=date(2025, 6, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
        )
        assert booking.pk is not None

    def test_status_choices_default(self):
        from datetime import date, time
        booking = VenueBooking.objects.create(
            requester_name="Jane Doe",
            requester_phone="+50944444444",
            event_type="Atelier",
            event_date=date(2025, 7, 1),
            start_time=time(10, 0),
            end_time=time(12, 0),
        )
        assert booking.status == VenueBooking.Status.REQUESTED

    def test_str(self):
        from datetime import date, time
        booking = VenueBooking.objects.create(
            requester_name="Bob",
            requester_phone="+50955555555",
            event_type="Séminaire",
            event_date=date(2025, 8, 10),
            start_time=time(14, 0),
            end_time=time(16, 0),
        )
        assert str(booking) == "Séminaire - 2025-08-10"


# ── PaymentProvider ──────────────────────────────────────

@pytest.mark.django_db
class TestPaymentProviderModel:
    def test_creation(self):
        provider = PaymentProvider.objects.create(
            name="MonCash Test",
            provider_type=PaymentProvider.ProviderType.MONCASH,
        )
        assert provider.pk is not None

    def test_provider_type_choices(self):
        provider = PaymentProvider.objects.create(
            name="Virement",
            provider_type=PaymentProvider.ProviderType.BANK,
        )
        assert provider.provider_type == "bank"
        assert provider.get_provider_type_display() == "Virement bancaire"


# ── Payment ──────────────────────────────────────────────

@pytest.mark.django_db
class TestPaymentModel:
    def test_creation(self):
        from datetime import date, time
        provider = PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH)
        payment = Payment.objects.create(
            purpose=Payment.Purpose.OTHER,
            provider=provider,
            payer_name="Client Test",
            payer_phone="+50966666666",
            amount_htg=1000,
        )
        assert payment.pk is not None

    def test_reference_auto_generation(self):
        provider = PaymentProvider.objects.create(name="Test", provider_type=PaymentProvider.ProviderType.MANUAL)
        payment = Payment.objects.create(
            purpose=Payment.Purpose.VENUE,
            provider=provider,
            payer_name="Client Ref",
            payer_phone="+50977777777",
            amount_htg=500,
        )
        assert payment.reference.startswith("IMSO-VEN-")

    def test_status_cascade_to_booking(self):
        from datetime import date, time
        provider = PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH)
        booking = VenueBooking.objects.create(
            requester_name="Booking Test",
            requester_phone="+50988888888",
            event_type="Test",
            event_date=date(2025, 9, 1),
            start_time=time(8, 0),
            end_time=time(18, 0),
            status=VenueBooking.Status.PAYMENT_PENDING,
        )
        payment = Payment.objects.create(
            purpose=Payment.Purpose.VENUE,
            provider=provider,
            payer_name="Payeur",
            payer_phone="+50999999999",
            amount_htg=2000,
            venue_booking=booking,
            status=Payment.Status.PENDING,
        )
        payment.status = Payment.Status.PAID
        payment.save()
        booking.refresh_from_db()
        assert booking.status == VenueBooking.Status.ADMIN_REVIEW

    def test_status_cascade_to_enrollment(self):
        gei = GEI.objects.create(name="GEI", city="Ville")
        member = Member.objects.create(first_name="Test", last_name="User", phone="+50900000003", gei=gei)
        course = Course.objects.create(title="Cours Cascade", category="Test", instructor="Prof", city="Ville")
        enrollment = Enrollment.objects.create(member=member, course=course)
        provider = PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH)
        payment = Payment.objects.create(
            purpose=Payment.Purpose.COURSE,
            provider=provider,
            payer_name="Test",
            payer_phone="+50911111112",
            amount_htg=3000,
            enrollment=enrollment,
            status=Payment.Status.PENDING,
        )
        payment.status = Payment.Status.PAID
        payment.save()
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.Status.CONFIRMED


# ── ContactRequest ───────────────────────────────────────

@pytest.mark.django_db
class TestContactRequestModel:
    def test_creation(self):
        contact = ContactRequest.objects.create(
            full_name="Contact Test",
            phone="+50922222223",
            email="contact@test.com",
            subject=ContactRequest.Subject.MEMBERSHIP,
        )
        assert contact.pk is not None

    def test_str(self):
        contact = ContactRequest.objects.create(
            full_name="Marie Claire",
            phone="+50933333334",
            subject=ContactRequest.Subject.COURSE,
        )
        assert str(contact) == "Marie Claire - Inscription a un cours"


# ── AdminNotification ────────────────────────────────────

@pytest.mark.django_db
class TestAdminNotificationModel:
    def test_creation(self):
        notif = AdminNotification.objects.create(
            message="Test notification",
            notification_type=AdminNotification.NotificationType.NEW_BOOKING,
        )
        assert notif.pk is not None

    def test_str(self):
        notif = AdminNotification.objects.create(
            message="Nouvelle réservation",
            notification_type=AdminNotification.NotificationType.NEW_BOOKING,
        )
        assert str(notif) == "[Nouvelle réservation] Nouvelle réservation"


# ── Admin API Tests ──────────────────────────────────────

@pytest.mark.django_db
class TestAdminEndpoints:
    def _login(self, client):
        user = User.objects.create_superuser("admin", "admin@test.com", "password123")
        client.force_login(user)

    def test_summary_redirect_without_auth(self):
        client = Client()
        response = client.get(reverse("adminpanel:summary"))
        assert response.status_code == 302

    def test_members_redirect_without_auth(self):
        client = Client()
        response = client.get(reverse("adminpanel:member-list"))
        assert response.status_code == 302

    def test_summary_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:summary"))
        assert response.status_code == 200

    def test_members_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:member-list"))
        assert response.status_code == 200

    def test_courses_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:course-list"))
        assert response.status_code == 200

    def test_bookings_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:booking-list"))
        assert response.status_code == 200

    def test_payments_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:payment-list"))
        assert response.status_code == 200

    def test_geis_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:gei-list"))
        assert response.status_code == 200

    def test_providers_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:provider-list"))
        assert response.status_code == 200

    def test_enrollments_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:enrollment-list"))
        assert response.status_code == 200

    def test_notifications_with_auth(self):
        client = Client()
        self._login(client)
        response = client.get(reverse("adminpanel:notification-list"))
        assert response.status_code == 200

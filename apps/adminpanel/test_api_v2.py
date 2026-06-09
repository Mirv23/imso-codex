import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

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
from .models import EncryptedCharField

pytestmark = pytest.mark.django_db

# EncryptedCharField.from_db_value has a bug: it doesn't strip the "enc:" prefix.
# Patch it so DRF endpoint tests for PaymentProvider work correctly.
_orig_from_db_value = EncryptedCharField.from_db_value


def _patched_from_db_value(self, value, expression, connection):
    if value is not None and isinstance(value, str) and value.startswith("enc:"):
        value = value[4:]
    return _orig_from_db_value(self, value, expression, connection)


EncryptedCharField.from_db_value = _patched_from_db_value


# ── Helpers ─────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client):
    user = User.objects.create_superuser("admin", "admin@test.com", "password123")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def gei():
    return GEI.objects.create(name="Test GEI", city="Port-au-Prince")


@pytest.fixture
def member(gei):
    return Member.objects.create(
        first_name="Jean",
        last_name="Dupont",
        phone="+50912345678",
        email="jean@test.com",
        gei=gei,
        status=Member.Status.ACTIVE,
        monthly_saving_htg=500,
    )


@pytest.fixture
def course():
    return Course.objects.create(
        title="Python Avancé",
        category="Programmation",
        instructor="M. Jean",
        city="Port-au-Prince",
        price_htg=5000,
        capacity=20,
    )


@pytest.fixture
def enrollment(member, course):
    return Enrollment.objects.create(member=member, course=course)


@pytest.fixture
def venue_booking():
    from datetime import date, time
    return VenueBooking.objects.create(
        requester_name="John Doe",
        requester_phone="+50933333333",
        event_type="Conférence",
        event_date=date(2025, 6, 15),
        start_time=time(9, 0),
        end_time=time(17, 0),
    )


@pytest.fixture
def payment_provider():
    return PaymentProvider.objects.create(
        name="MonCash Test",
        provider_type=PaymentProvider.ProviderType.MONCASH,
    )


@pytest.fixture
def payment(payment_provider):
    return Payment.objects.create(
        purpose=Payment.Purpose.OTHER,
        provider=payment_provider,
        payer_name="Client Test",
        payer_phone="+50966666666",
        amount_htg=1000,
    )


@pytest.fixture
def contact_request():
    return ContactRequest.objects.create(
        full_name="Contact Test",
        phone="+50922222223",
        email="contact@test.com",
        subject=ContactRequest.Subject.MEMBERSHIP,
    )


@pytest.fixture
def admin_notification():
    return AdminNotification.objects.create(
        message="Test notification",
        notification_type=AdminNotification.NotificationType.NEW_BOOKING,
    )


# ── Authentication ──────────────────────────────────────────────

class TestAPIAuth:
    def test_401_without_auth(self, api_client):
        response = api_client.get(reverse("adminpanel:v2-gei-list"))
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_200_with_auth(self, auth_client):
        response = auth_client.get(reverse("adminpanel:v2-gei-list"))
        assert response.status_code == status.HTTP_200_OK


# ── GEI ─────────────────────────────────────────────────────────

class TestAPIGEI:
    def test_list(self, auth_client, gei):
        response = auth_client.get(reverse("adminpanel:v2-gei-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, gei):
        response = auth_client.get(reverse("adminpanel:v2-gei-detail", args=[gei.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test GEI"

    def test_create(self, auth_client):
        response = auth_client.post(
            reverse("adminpanel:v2-gei-list"),
            {"name": "New GEI", "city": "Jacmel"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New GEI"

    def test_update(self, auth_client, gei):
        response = auth_client.put(
            reverse("adminpanel:v2-gei-detail", args=[gei.pk]),
            {"name": "Updated GEI", "city": "Cap-Haïtien"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated GEI"

    def test_delete(self, auth_client, gei):
        response = auth_client.delete(reverse("adminpanel:v2-gei-detail", args=[gei.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert GEI.objects.count() == 0

    def test_search(self, auth_client, gei):
        response = auth_client.get(reverse("adminpanel:v2-gei-list"), {"search": "Test"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, gei):
        response = auth_client.get(reverse("adminpanel:v2-gei-list"), {"ordering": "name"})
        assert response.status_code == status.HTTP_200_OK


# ── Member ──────────────────────────────────────────────────────

class TestAPIMember:
    def test_list(self, auth_client, member):
        response = auth_client.get(reverse("adminpanel:v2-member-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, member):
        response = auth_client.get(reverse("adminpanel:v2-member-detail", args=[member.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Jean"

    def test_create(self, auth_client, gei):
        response = auth_client.post(
            reverse("adminpanel:v2-member-list"),
            {
                "first_name": "Alice",
                "last_name": "Midi",
                "phone": "+50922222222",
                "gei": gei.pk,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Alice"

    def test_update(self, auth_client, member):
        response = auth_client.put(
            reverse("adminpanel:v2-member-detail", args=[member.pk]),
            {
                "first_name": "Jean",
                "last_name": "Mis à jour",
                "phone": "+50912345678",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["last_name"] == "Mis à jour"

    def test_delete(self, auth_client, member):
        response = auth_client.delete(reverse("adminpanel:v2-member-detail", args=[member.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Member.objects.count() == 0

    def test_search(self, auth_client, member):
        response = auth_client.get(reverse("adminpanel:v2-member-list"), {"search": "Jean"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, member):
        response = auth_client.get(reverse("adminpanel:v2-member-list"), {"ordering": "last_name"})
        assert response.status_code == status.HTTP_200_OK


# ── Course ──────────────────────────────────────────────────────

class TestAPICourse:
    def test_list(self, auth_client, course):
        response = auth_client.get(reverse("adminpanel:v2-course-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, course):
        response = auth_client.get(reverse("adminpanel:v2-course-detail", args=[course.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Python Avancé"

    def test_create(self, auth_client):
        response = auth_client.post(
            reverse("adminpanel:v2-course-list"),
            {
                "title": "Django Avancé",
                "category": "Programmation",
                "instructor": "Mme Anne",
                "city": "Cap-Haïtien",
                "price_htg": 7500,
                "capacity": 15,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Django Avancé"

    def test_update(self, auth_client, course):
        response = auth_client.put(
            reverse("adminpanel:v2-course-detail", args=[course.pk]),
            {
                "title": "Python Intermédiaire",
                "category": "Programmation",
                "instructor": "M. Jean",
                "city": "Port-au-Prince",
                "price_htg": 6000,
                "capacity": 25,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Python Intermédiaire"

    def test_delete(self, auth_client, course):
        response = auth_client.delete(reverse("adminpanel:v2-course-detail", args=[course.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Course.objects.count() == 0

    def test_search(self, auth_client, course):
        response = auth_client.get(reverse("adminpanel:v2-course-list"), {"search": "Python"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, course):
        response = auth_client.get(reverse("adminpanel:v2-course-list"), {"ordering": "title"})
        assert response.status_code == status.HTTP_200_OK


# ── Enrollment ──────────────────────────────────────────────────

class TestAPIEnrollment:
    def test_list(self, auth_client, enrollment):
        response = auth_client.get(reverse("adminpanel:v2-enrollment-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, enrollment):
        response = auth_client.get(reverse("adminpanel:v2-enrollment-detail", args=[enrollment.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["member"]["first_name"] == "Jean"

    def test_search(self, auth_client, enrollment):
        response = auth_client.get(reverse("adminpanel:v2-enrollment-list"), {"search": "Jean"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, enrollment):
        response = auth_client.get(reverse("adminpanel:v2-enrollment-list"), {"ordering": "created_at"})
        assert response.status_code == status.HTTP_200_OK


# ── VenueBooking ───────────────────────────────────────────────

class TestAPIVenueBooking:
    def test_list(self, auth_client, venue_booking):
        response = auth_client.get(reverse("adminpanel:v2-booking-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, venue_booking):
        response = auth_client.get(reverse("adminpanel:v2-booking-detail", args=[venue_booking.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["requester_name"] == "John Doe"

    def test_create(self, auth_client):
        from datetime import date, time
        response = auth_client.post(
            reverse("adminpanel:v2-booking-list"),
            {
                "requester_name": "Jane Doe",
                "requester_phone": "+50944444444",
                "event_type": "Atelier",
                "event_date": "2025-07-01",
                "start_time": "10:00:00",
                "end_time": "12:00:00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["requester_name"] == "Jane Doe"

    def test_update(self, auth_client, venue_booking):
        response = auth_client.put(
            reverse("adminpanel:v2-booking-detail", args=[venue_booking.pk]),
            {
                "requester_name": "John Updated",
                "requester_phone": "+50933333333",
                "event_type": "Séminaire",
                "event_date": "2025-06-15",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["requester_name"] == "John Updated"

    def test_delete(self, auth_client, venue_booking):
        response = auth_client.delete(reverse("adminpanel:v2-booking-detail", args=[venue_booking.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert VenueBooking.objects.count() == 0

    def test_search(self, auth_client, venue_booking):
        response = auth_client.get(reverse("adminpanel:v2-booking-list"), {"search": "John"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, venue_booking):
        response = auth_client.get(reverse("adminpanel:v2-booking-list"), {"ordering": "event_date"})
        assert response.status_code == status.HTTP_200_OK


# ── PaymentProvider ─────────────────────────────────────────────

class TestAPIPaymentProvider:
    def test_list(self, auth_client, payment_provider):
        response = auth_client.get(reverse("adminpanel:v2-provider-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, payment_provider):
        response = auth_client.get(reverse("adminpanel:v2-provider-detail", args=[payment_provider.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "MonCash Test"

    def test_create(self, auth_client):
        response = auth_client.post(
            reverse("adminpanel:v2-provider-list"),
            {"name": "NatCash", "provider_type": "natcash"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "NatCash"

    def test_update(self, auth_client, payment_provider):
        response = auth_client.put(
            reverse("adminpanel:v2-provider-detail", args=[payment_provider.pk]),
            {"name": "MonCash Updated", "provider_type": "moncash"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "MonCash Updated"

    def test_delete(self, auth_client, payment_provider):
        response = auth_client.delete(reverse("adminpanel:v2-provider-detail", args=[payment_provider.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert PaymentProvider.objects.count() == 0

    def test_search(self, auth_client, payment_provider):
        response = auth_client.get(reverse("adminpanel:v2-provider-list"), {"search": "MonCash"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, payment_provider):
        response = auth_client.get(reverse("adminpanel:v2-provider-list"), {"ordering": "name"})
        assert response.status_code == status.HTTP_200_OK


# ── Payment ─────────────────────────────────────────────────────

class TestAPIPayment:
    def test_list(self, auth_client, payment):
        response = auth_client.get(reverse("adminpanel:v2-payment-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, payment):
        response = auth_client.get(reverse("adminpanel:v2-payment-detail", args=[payment.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["payer_name"] == "Client Test"

    def test_create(self, auth_client, payment_provider):
        response = auth_client.post(
            reverse("adminpanel:v2-payment-list"),
            {
                "purpose": "other",
                "provider": payment_provider.pk,
                "payer_name": "New Client",
                "payer_phone": "+50977777777",
                "amount_htg": 2000,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["payer_name"] == "New Client"

    def test_update(self, auth_client, payment):
        response = auth_client.put(
            reverse("adminpanel:v2-payment-detail", args=[payment.pk]),
            {
                "purpose": "other",
                "provider": payment.provider_id,
                "payer_name": "Updated Client",
                "payer_phone": "+50966666666",
                "amount_htg": 1500,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["payer_name"] == "Updated Client"

    def test_delete(self, auth_client, payment):
        response = auth_client.delete(reverse("adminpanel:v2-payment-detail", args=[payment.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Payment.objects.count() == 0

    def test_search(self, auth_client, payment):
        response = auth_client.get(reverse("adminpanel:v2-payment-list"), {"search": "Client"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, payment):
        response = auth_client.get(reverse("adminpanel:v2-payment-list"), {"ordering": "amount_htg"})
        assert response.status_code == status.HTTP_200_OK


# ── ContactRequest ──────────────────────────────────────────────

class TestAPIContactRequest:
    def test_list(self, auth_client, contact_request):
        response = auth_client.get(reverse("adminpanel:v2-contact-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, contact_request):
        response = auth_client.get(reverse("adminpanel:v2-contact-detail", args=[contact_request.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Contact Test"

    def test_create(self, auth_client):
        response = auth_client.post(
            reverse("adminpanel:v2-contact-list"),
            {
                "full_name": "New Contact",
                "phone": "+50988888888",
                "subject": "membership",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["full_name"] == "New Contact"

    def test_update(self, auth_client, contact_request):
        response = auth_client.put(
            reverse("adminpanel:v2-contact-detail", args=[contact_request.pk]),
            {
                "full_name": "Updated Contact",
                "phone": "+50922222223",
                "subject": "course",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Updated Contact"

    def test_delete(self, auth_client, contact_request):
        response = auth_client.delete(reverse("adminpanel:v2-contact-detail", args=[contact_request.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ContactRequest.objects.count() == 0

    def test_search(self, auth_client, contact_request):
        response = auth_client.get(reverse("adminpanel:v2-contact-list"), {"search": "Contact"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_ordering(self, auth_client, contact_request):
        response = auth_client.get(reverse("adminpanel:v2-contact-list"), {"ordering": "created_at"})
        assert response.status_code == status.HTTP_200_OK


# ── AdminNotification (ReadOnly) ────────────────────────────────

class TestAPIAdminNotification:
    def test_list(self, auth_client, admin_notification):
        response = auth_client.get(reverse("adminpanel:v2-notification-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_detail(self, auth_client, admin_notification):
        response = auth_client.get(reverse("adminpanel:v2-notification-detail", args=[admin_notification.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Test notification"

    def test_mark_read(self, auth_client, admin_notification):
        response = auth_client.post(
            reverse("adminpanel:v2-notification-mark-read", args=[admin_notification.pk]),
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["ok"] is True
        admin_notification.refresh_from_db()
        assert admin_notification.is_read is True

    def test_mark_all_read(self, auth_client):
        AdminNotification.objects.create(
            message="Unread 1",
            notification_type=AdminNotification.NotificationType.NEW_BOOKING,
        )
        AdminNotification.objects.create(
            message="Unread 2",
            notification_type=AdminNotification.NotificationType.NEW_PAYMENT,
        )
        response = auth_client.post(reverse("adminpanel:v2-notification-mark-all-read"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["ok"] is True
        assert AdminNotification.objects.filter(is_read=False).count() == 0


# ── Dashboard Summary ──────────────────────────────────────────

class TestAPIDashboardSummary:
    def test_summary(self, auth_client):
        response = auth_client.get(reverse("adminpanel:v2-dashboard-summary"))
        assert response.status_code == status.HTTP_200_OK
        assert "active_members" in response.data
        assert "active_gei" in response.data
        assert "total_revenue_htg" in response.data

    def test_summary_returns_counts(self, auth_client, gei, member, course):
        response = auth_client.get(reverse("adminpanel:v2-dashboard-summary"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_gei"] >= 1
        assert response.data["total_members"] >= 1
        assert response.data["total_courses"] >= 1

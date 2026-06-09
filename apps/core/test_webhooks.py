import json
from datetime import date, time

import pytest
from django.test import Client
from django.urls import reverse

from apps.adminpanel.models import (
    Course,
    Enrollment,
    GEI,
    Member,
    Payment,
    PaymentProvider,
    VenueBooking,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _set_webhook_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "whsec_test")


@pytest.fixture
def provider():
    return PaymentProvider.objects.create(
        name="Stripe Test",
        provider_type=PaymentProvider.ProviderType.STRIPE,
    )


@pytest.fixture
def provider_moncash():
    return PaymentProvider.objects.create(
        name="MonCash Test",
        provider_type=PaymentProvider.ProviderType.MONCASH,
    )


@pytest.fixture
def booking():
    return VenueBooking.objects.create(
        requester_name="Booking Test",
        requester_phone="+50988888888",
        event_type="Test",
        event_date=date(2025, 9, 1),
        start_time=time(8, 0),
        end_time=time(18, 0),
        status=VenueBooking.Status.PAYMENT_PENDING,
    )


@pytest.fixture
def enrollment():
    gei = GEI.objects.create(name="GEI", city="Ville")
    member = Member.objects.create(first_name="Test", last_name="User", phone="+50900000001", gei=gei)
    course = Course.objects.create(title="Cours Test", category="Test", instructor="Prof", city="Ville")
    return Enrollment.objects.create(member=member, course=course)


@pytest.fixture
def payment(provider, booking):
    return Payment.objects.create(
        purpose=Payment.Purpose.VENUE,
        provider=provider,
        payer_name="Test",
        payer_phone="+50911111111",
        amount_htg=2000,
        venue_booking=booking,
        status=Payment.Status.PENDING,
        external_reference="pi_123456",
    )


@pytest.fixture
def payment_enrollment(provider_moncash, enrollment):
    return Payment.objects.create(
        purpose=Payment.Purpose.COURSE,
        provider=provider_moncash,
        payer_name="Student",
        payer_phone="+50922222222",
        amount_htg=3000,
        enrollment=enrollment,
        status=Payment.Status.PENDING,
        external_reference="txn_789",
    )


# ── Stripe Webhook ─────────────────────────────────────────────

class TestWebhookStripe:
    def test_success_marks_payment_paid(self, client, payment):
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_123456"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["payment"] == payment.reference
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.paid_at is not None

    def test_invalid_secret_returns_401(self, client):
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_123456"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="wrong_secret",
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_no_payment_found(self, client):
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_nonexistent"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment"] is None

    def test_already_paid(self, client, payment):
        payment.status = Payment.Status.PAID
        payment.save()
        paid_at_before = payment.paid_at
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_123456"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
        assert payment.paid_at == paid_at_before

    def test_cascade_booking_to_admin_review(self, client, payment, booking):
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_123456"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == VenueBooking.Status.ADMIN_REVIEW

    def test_no_external_reference(self, client):
        response = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"foo": "bar"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment"] is None


# ── MonCash Webhook ────────────────────────────────────────────

class TestWebhookMonCash:
    def test_success_marks_payment_paid(self, client, payment_enrollment):
        response = client.post(
            reverse("core:webhook", args=["moncash"]),
            data=json.dumps({"transactionId": "txn_789"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["payment"] == payment_enrollment.reference
        payment_enrollment.refresh_from_db()
        assert payment_enrollment.status == Payment.Status.PAID

    def test_invalid_secret_returns_401(self, client):
        response = client.post(
            reverse("core:webhook", args=["moncash"]),
            data=json.dumps({"transactionId": "txn_789"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="bad_secret",
        )
        assert response.status_code == 401

    def test_cascade_enrollment_to_confirmed(self, client, payment_enrollment, enrollment):
        response = client.post(
            reverse("core:webhook", args=["moncash"]),
            data=json.dumps({"transactionId": "txn_789"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        enrollment.refresh_from_db()
        assert enrollment.status == Enrollment.Status.CONFIRMED

    def test_no_payment_found(self, client):
        response = client.post(
            reverse("core:webhook", args=["moncash"]),
            data=json.dumps({"transactionId": "txn_invalid"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment"] is None


# ── Other provider ─────────────────────────────────────────────

class TestWebhookOther:
    def test_unknown_provider(self, client):
        response = client.post(
            reverse("core:webhook", args=["unknown"]),
            data=json.dumps({"some": "data"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

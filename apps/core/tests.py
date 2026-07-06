import json
from datetime import date, time

import pytest
from django.test import Client
from django.urls import reverse

from apps.adminpanel.models import Course, Enrollment, GEI, Member, Payment, PaymentProvider, VenueBooking


@pytest.mark.django_db
class TestPublicAPI:
    @pytest.fixture(autouse=True)
    def _set_payment_key(self, monkeypatch):
        monkeypatch.setenv("PAYMENT_CONFIRM_KEY", "test-key")

    def test_healthcheck(self):
        client = Client()
        response = client.get(reverse("core:healthcheck"))
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "imso"

    def test_contact_request_valid(self):
        client = Client()
        response = client.post(
            reverse("core:contact_request_create"),
            data=json.dumps({
                "full_name": "Test User",
                "phone": "+50912345678",
                "subject": "membership",
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["ok"] is True
        assert "id" in data

    def test_contact_request_invalid(self):
        client = Client()
        response = client.post(
            reverse("core:contact_request_create"),
            data=json.dumps({"phone": "+50912345678"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False
        assert "errors" in data

    def test_venue_booking_valid(self):
        client = Client()
        response = client.post(
            reverse("core:venue_booking_create"),
            data=json.dumps({
                "requester_name": "Test Book",
                "requester_phone": "+50987654321",
                "event_type": "Conférence",
                "event_date": "2025-12-01",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "guest_count": 10,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["ok"] is True
        assert "id" in data

    def test_course_enrollment_valid(self):
        gei = GEI.objects.create(name="GEI Test", city="Ville")
        member = Member.objects.create(first_name="Test", last_name="User", phone="+50900000001", gei=gei)
        course = Course.objects.create(
            title="Cours API",
            category="Test",
            instructor="Prof",
            city="Ville",
            price_htg=1000,
            capacity=10,
        )
        client = Client()
        response = client.post(
            reverse("core:course_enrollment_create"),
            data=json.dumps({
                "full_name": "Test User",
                "phone": "+50900000001",
                "course_id": course.id,
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["ok"] is True
        assert "id" in data

    def test_providers_list(self):
        PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH, is_active=True)
        client = Client()
        response = client.get(reverse("core:active_providers"))
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_courses_list(self):
        Course.objects.create(title="Cours Pub", category="Test", instructor="Prof", city="Ville", is_active=True)
        client = Client()
        response = client.get(reverse("core:active_courses"))
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_confirm_manual_without_reference(self):
        client = Client()
        response = client.post(
            reverse("core:payment_confirm_manual"),
            data=json.dumps({}),
            content_type="application/json",
            HTTP_X_API_KEY="test-key",
        )
        assert response.status_code == 400
        data = response.json()
        assert data["ok"] is False

    def test_confirm_manual_with_reference(self):
        provider = PaymentProvider.objects.create(name="Test", provider_type=PaymentProvider.ProviderType.MANUAL)
        payment = Payment.objects.create(
            purpose=Payment.Purpose.OTHER,
            provider=provider,
            payer_name="Test",
            payer_phone="+50911111111",
            amount_htg=500,
        )
        client = Client()
        response = client.post(
            reverse("core:payment_confirm_manual"),
            data=json.dumps({"payment_reference": payment.reference}),
            content_type="application/json",
            HTTP_X_API_KEY="test-key",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    def test_payment_confirmation(self):
        provider = PaymentProvider.objects.create(name="Test", provider_type=PaymentProvider.ProviderType.MANUAL)
        payment = Payment.objects.create(
            purpose=Payment.Purpose.OTHER,
            provider=provider,
            payer_name="Test",
            payer_phone="+50922222222",
            amount_htg=750,
        )
        client = Client()
        response = client.get(
            reverse("core:payment_confirmation", kwargs={"reference": payment.reference})
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reference"] == payment.reference

    def test_payment_link_uses_signed_token_not_sequential_id(self):
        """La page de paiement n'accepte plus l'id séquentiel (fuite de PII par
        énumération) : seul un jeton signé résout, et jamais pour un autre type."""
        from apps.core.payment_tokens import make_payment_token

        member = Member.objects.create(
            first_name="Jean", last_name="Privé", email="j@ex.com", phone="+50911112222"
        )
        course = Course.objects.create(title="Cours", price_htg=500)
        enr = Enrollment.objects.create(
            member=member, course=course, status=Enrollment.Status.PENDING
        )
        client = Client()
        # id brut -> 404 (plus énumérable)
        assert client.get(f"/paiement/cours/{enr.id}/").status_code == 404
        # jeton falsifié -> 404
        assert client.get("/paiement/cours/nimportequoi/").status_code == 404
        # jeton signé pour un AUTRE type -> 404
        other = make_payment_token("reservation", enr.id)
        assert client.get(f"/paiement/cours/{other}/").status_code == 404
        # jeton valide -> 200 et pré-remplit le nom
        good = make_payment_token("cours", enr.id)
        resp = client.get(f"/paiement/cours/{good}/")
        assert resp.status_code == 200
        assert b"Jean" in resp.content

    def test_rate_limit_after_11_requests(self):
        client = Client(REMOTE_ADDR="192.0.2.1")
        url = reverse("core:contact_request_create")
        for _ in range(10):
            response = client.post(
                url,
                data=json.dumps({
                    "full_name": "Rate Test",
                    "phone": "+50900000001",
                    "subject": "membership",
                }),
                content_type="application/json",
            )
            if _ < 9:
                continue
        response = client.post(
            url,
            data=json.dumps({"full_name": "Rate Test", "phone": "+50900000002", "subject": "membership"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_cors_headers_on_healthcheck(self):
        client = Client()
        response = client.get(reverse("core:healthcheck"), HTTP_ORIGIN="https://example.com")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" not in response

        response = client.get(reverse("core:healthcheck"), HTTP_ORIGIN="https://imsohaiti.com")
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" not in response


@pytest.mark.django_db
class TestAdminEndpoints:
    def _login(self, client):
        from django.contrib.auth.models import User
        user = User.objects.create_superuser("admin", "admin@test.com", "password123")
        client.force_login(user)

    def test_summary_redirect_without_auth(self):
        # API anonyme -> 401 JSON (plus 302 vers login) : correctif dashboard vide.
        client = Client()
        response = client.get(reverse("adminpanel:summary"))
        assert response.status_code == 401

    def test_members_redirect_without_auth(self):
        client = Client()
        response = client.get(reverse("adminpanel:member-list"))
        assert response.status_code == 401

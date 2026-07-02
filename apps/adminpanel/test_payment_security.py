"""Tests de la sécurité paiement (S1 webhook, S2 chiffrement des secrets)."""

import json

import pytest
from django.db import connection
from django.test import Client
from django.urls import reverse

from .models import Payment, PaymentProvider


# ── S2 : chiffrement des secrets au repos ────────────────────────

@pytest.mark.django_db
class TestSecretEncryption:
    def test_secret_roundtrip_and_encrypted_at_rest(self):
        p = PaymentProvider.objects.create(
            name="MonCash", provider_type=PaymentProvider.ProviderType.MONCASH,
            api_secret_key="SECRET-ABC-123",
        )
        p.refresh_from_db()
        # Déchiffrement transparent à la lecture.
        assert p.api_secret_key == "SECRET-ABC-123"
        # En base, la valeur est chiffrée (Fernet) — jamais en clair.
        with connection.cursor() as cur:
            cur.execute(
                "SELECT api_secret_key FROM adminpanel_paymentprovider WHERE id = %s",
                [p.id],
            )
            raw = cur.fetchone()[0]
        assert raw.startswith("fer:")
        assert "SECRET-ABC-123" not in raw

    def test_empty_secret_stays_empty(self):
        p = PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH)
        p.refresh_from_db()
        assert p.api_secret_key == ""


# ── S1 : webhook durci ───────────────────────────────────────────

@pytest.mark.django_db
class TestWebhookHardening:
    def _payment(self):
        provider = PaymentProvider.objects.create(
            name="Stripe", provider_type=PaymentProvider.ProviderType.STRIPE
        )
        return Payment.objects.create(
            purpose=Payment.Purpose.OTHER, provider=provider, payer_name="X",
            amount_htg=2000, status=Payment.Status.PENDING, external_reference="pi_amt",
        )

    def test_fail_closed_without_secret(self, monkeypatch):
        monkeypatch.delenv("WEBHOOK_SECRET", raising=False)
        client = Client()
        resp = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_amt"}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="anything",
        )
        assert resp.status_code == 503

    def test_amount_mismatch_rejected(self, monkeypatch):
        monkeypatch.setenv("WEBHOOK_SECRET", "whsec_test")
        payment = self._payment()
        client = Client()
        resp = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_amt", "amount_htg": 9999}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert resp.status_code == 400
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PENDING  # non validé

    def test_amount_match_accepted(self, monkeypatch):
        monkeypatch.setenv("WEBHOOK_SECRET", "whsec_test")
        payment = self._payment()
        client = Client()
        resp = client.post(
            reverse("core:webhook", args=["stripe"]),
            data=json.dumps({"payment_intent": "pi_amt", "amount_htg": 2000}),
            content_type="application/json",
            HTTP_X_WEBHOOK_SECRET="whsec_test",
        )
        assert resp.status_code == 200
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID

"""Tests de regression des correctifs de stabilite (audit multi-agents).

Chaque test verrouille un defaut confirme puis corrige : entrees qui plantaient
en 500, doublons, non-idempotence. Objectif : empecher toute regression future.
"""
import json

import pytest
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

from apps.adminpanel.models import (
    Course, Enrollment, Member, Order, OrderItem, Payment, PaymentProvider, Product,
)
from apps.core.payment_tokens import make_payment_token

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _webhook_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "whsec_test")


# ── Webhook : external_reference en double ne plante plus (MultipleObjectsReturned) ──
def test_webhook_duplicate_external_reference_no_500():
    prov = PaymentProvider.objects.create(name="Stripe", provider_type=PaymentProvider.ProviderType.STRIPE)
    for _ in range(2):
        Payment.objects.create(
            purpose=Payment.Purpose.OTHER, provider=prov, payer_name="X",
            amount_htg=100, status=Payment.Status.PENDING, external_reference="DUP-REF",
        )
    c = Client()
    resp = c.post(
        reverse("core:webhook", args=["stripe"]),
        data=json.dumps({"payment_intent": "DUP-REF"}),
        content_type="application/json",
        HTTP_X_WEBHOOK_SECRET="whsec_test",
    )
    assert resp.status_code == 200  # etait 500 (MultipleObjectsReturned)
    # Un des deux paiements PENDING est passe a PAID (selection deterministe).
    assert Payment.objects.filter(external_reference="DUP-REF", status=Payment.Status.PAID).count() == 1


# ── Inscription cours : double soumission idempotente (plus d'IntegrityError 500) ──
def test_course_enrollment_double_submit_is_idempotent():
    course = Course.objects.create(title="Cours", category="Cat", instructor="P", city="V")
    c = Client()
    payload = {"full_name": "Jean Test", "phone": "+50912345678", "course_id": course.id}
    r1 = c.post("/api/course-enrollments/", data=json.dumps(payload), content_type="application/json")
    r2 = c.post("/api/course-enrollments/", data=json.dumps(payload), content_type="application/json")
    assert r1.status_code == 201
    assert r2.status_code == 200  # reutilise l'inscription existante, etait 500
    assert Enrollment.objects.filter(course=course).count() == 1


# ── Paiement : provider_id non numerique -> 400 (etait 500) ──
def test_payment_provider_id_non_numeric_returns_400():
    course = Course.objects.create(title="C", category="Cat", instructor="P", city="V", price_htg=100)
    member = Member.objects.create(first_name="A", last_name="B", phone="+509000")
    enr = Enrollment.objects.create(member=member, course=course, status=Enrollment.Status.PENDING)
    token = make_payment_token("cours", enr.id)
    c = Client()
    resp = c.post(
        f"/api/paiement/cours/{token}/",
        data=json.dumps({"provider_id": "abc"}),
        content_type="application/json",
    )
    assert resp.status_code == 400


# ── Liste admin : per_page=0 ne plante plus (ZeroDivisionError) ──
def test_admin_list_per_page_zero_no_500():
    admin = User.objects.create_superuser("adm", "adm@x.com", "pw123456789")
    c = Client()
    c.force_login(admin)
    for pp in ("0", "-3", "abc"):
        assert c.get(f"/dashboard/api/members/?per_page={pp}").status_code == 200


# ── Stock : la decrementation sur commande PAID est idempotente (pas de survente) ──
def test_order_stock_decrement_is_idempotent():
    prov = PaymentProvider.objects.create(name="Cash", provider_type=PaymentProvider.ProviderType.CASH)
    product = Product.objects.create(name="Livre", price_htg=500, stock=10)
    order = Order.objects.create(customer_name="C", customer_phone="509", delivery_address="X")
    OrderItem.objects.create(order=order, product=product, product_name=product.name, quantity=3, unit_price_htg=500)
    order.recompute_total()
    order.save()
    # 1er passage a PAID -> stock 10 - 3 = 7
    order.status = Order.Status.PAID
    order.save()
    product.refresh_from_db()
    assert product.stock == 7
    # Re-sauvegarde alors que deja PAID -> pas de nouvelle decrementation
    order.save()
    product.refresh_from_db()
    assert product.stock == 7


# ── Reservation de salle : un creneau confirme devient indisponible ──
def _book(client, date, st, et):
    import json as _j
    return client.post("/api/venue-bookings/", _j.dumps({
        "requester_name": "Jean Test", "requester_phone": "509", "event_type": "Mariage",
        "event_date": date, "start_time": st, "end_time": et, "setup": "assis 40", "guest_count": 40,
    }), content_type="application/json")


def test_confirmed_booking_blocks_slot_and_prevents_double_booking():
    from apps.adminpanel.models import VenueBooking
    c = Client()
    r1 = _book(c, "2026-09-20", "18:00", "22:00")
    assert r1.status_code == 201
    bid = r1.json()["id"]
    # REQUESTED n'occupe pas encore le creneau
    av = c.get("/api/venue-availability/?from=2026-09-01&to=2026-09-30").json()
    assert av["occupied"].get("2026-09-20", []) == []
    # Une fois confirmee -> creneau occupe
    b = VenueBooking.objects.get(id=bid)
    b.status = VenueBooking.Status.CONFIRMED
    b.save()
    av = c.get("/api/venue-availability/?from=2026-09-01&to=2026-09-30").json()
    assert "soir" in av["occupied"].get("2026-09-20", [])
    # Double reservation (meme creneau ou chevauchement) -> 409
    assert _book(c, "2026-09-20", "18:00", "22:00").status_code == 409
    assert _book(c, "2026-09-20", "19:00", "21:00").status_code == 409
    # Autre creneau le meme jour -> autorise
    assert _book(c, "2026-09-20", "08:00", "12:00").status_code == 201

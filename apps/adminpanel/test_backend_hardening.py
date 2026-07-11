"""Regressions de robustesse backend (audit multi-agents, sprint 1).

Verifie qu'un corps JSON non-objet, une valeur hors-bornes ou une date invalide
renvoient 400 et JAMAIS 500, et que le filtre produits ne masque plus les actifs.
"""
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import Product

User = get_user_model()
pytestmark = pytest.mark.django_db


def _admin():
    u = User.objects.filter(username="hard_boss").first() or \
        User.objects.create_superuser("hard_boss", "h@x.com", "password123")
    c = Client()
    c.force_login(u)
    return c


# ── A-1 : corps JSON non-objet -> 400, jamais 500 ────────────────────────
@pytest.mark.parametrize("body", ["[1,2,3]", '"x"', "42", "true", "null"])
@pytest.mark.parametrize("ep", [
    "/api/contact-requests/",
    "/api/venue-bookings/",
    "/api/course-enrollments/",
    "/api/orders/",
])
def test_public_endpoints_reject_non_object_json(ep, body):
    r = Client().post(ep, data=body, content_type="application/json")
    assert r.status_code != 500, f"{ep} a renvoye 500 sur body {body}"
    assert r.status_code in (400, 403, 429)


def test_admin_booking_create_non_object_json_no_500():
    r = _admin().post("/dashboard/api/bookings/create/", data='"juststring"',
                      content_type="application/json")
    assert r.status_code == 400


# ── A-3 : entree trop longue tronquee, pas de DataError 500 ──────────────
def test_admin_booking_long_event_type_no_500():
    r = _admin().post("/dashboard/api/bookings/create/", data=json.dumps({
        "requester_name": "X", "event_date": "2026-09-20",
        "start_time": "08:00", "end_time": "12:00",
        "event_type": "E" * 300, "setup": "S" * 300,
    }), content_type="application/json")
    assert r.status_code in (201, 409)  # cree (tronque) ou creneau pris — jamais 500


# ── A-4 : date au bon format mais hors-plage -> 400, pas 500 ─────────────
def test_admin_booking_out_of_range_date_returns_400():
    r = _admin().post("/dashboard/api/bookings/create/", data=json.dumps({
        "requester_name": "X", "event_date": "2026-02-30",
        "start_time": "08:00", "end_time": "12:00", "event_type": "T",
    }), content_type="application/json")
    assert r.status_code == 400


# ── A-5 : ?active= vide ne masque plus les produits actifs ───────────────
def test_product_list_empty_active_filter_shows_active():
    Product.objects.create(name="KitVisible", price_htg=500, stock=5, is_active=True)
    d = _admin().get("/dashboard/api/products/?active=").json()
    assert d["total"] >= 1
    # filtre explicite toujours fonctionnel
    assert _admin().get("/dashboard/api/products/?active=1").json()["total"] >= 1
    assert _admin().get("/dashboard/api/products/?active=0").json()["total"] == 0

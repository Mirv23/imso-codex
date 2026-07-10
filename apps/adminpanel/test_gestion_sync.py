"""Tests de SYNCHRONISATION site public <-> panel admin pour les 3 sections de
gestion : Réservations, Inscriptions, Contacts.

Objectif : garantir qu'une donnée soumise depuis le SITE (formulaire public)
apparaît bien dans l'ADMIN, que les stats/filtres de l'admin la reflètent, et
qu'une action admin (confirmer/annuler/réinitialiser) se répercute sur le site
(ex. disponibilité du calendrier de réservation).
"""
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import Course, ContactRequest, Enrollment, VenueBooking

User = get_user_model()
pytestmark = pytest.mark.django_db

FUTURE = "2026-09-15"


def _admin():
    u = User.objects.create_superuser("boss_sync", "boss_sync@x.com", "password123")
    c = Client()
    c.force_login(u)
    return c


def _post(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


# ─────────────────────────── CONTACT ───────────────────────────
def test_contact_site_to_admin_sync():
    pub = Client()
    r = _post(pub, "/api/contact-requests/", {
        "full_name": "Marie Dupont", "phone": "+50938001122",
        "email": "marie@example.ht", "subject": "venue",
        "message": "Bonjour, je souhaite louer la salle pour un séminaire.",
    })
    assert r.status_code == 201, r.content

    admin = _admin()
    # 1) La demande apparaît dans la liste admin avec ses données.
    data = admin.get("/dashboard/api/contacts/").json()
    assert data["total"] == 1
    row = data["items"][0]
    assert row["full_name"] == "Marie Dupont"
    assert row["phone"] == "+50938001122"
    assert "séminaire" in row["message"]

    # 2) Les stats reflètent 1 non traité + le compteur par sujet.
    stats = admin.get("/dashboard/api/contacts/?stats=1").json()["stats"]
    assert stats["total"] == 1 and stats["unprocessed"] == 1
    assert stats["by_subject"].get("venue") == 1

    # 3) Filtre par sujet synchronisé.
    assert admin.get("/dashboard/api/contacts/?subject=venue").json()["total"] == 1
    assert admin.get("/dashboard/api/contacts/?subject=course").json()["total"] == 0

    # 4) Action admin « marquer traité » -> reflétée dans les stats.
    cid = ContactRequest.objects.get().id
    assert admin.put(f"/dashboard/api/contacts/{cid}/",
                     data=json.dumps({"is_processed": True}),
                     content_type="application/json").status_code == 200
    stats2 = admin.get("/dashboard/api/contacts/?stats=1").json()["stats"]
    assert stats2["unprocessed"] == 0


# ─────────────────────────── INSCRIPTION ───────────────────────────
def test_enrollment_site_to_admin_sync():
    course = Course.objects.create(title="Gestion d'épargne", category="Finance",
                                   instructor="Prof", city="PAP", price_htg=2000)
    pub = Client()
    r = _post(pub, "/api/course-enrollments/", {
        "full_name": "Jean Baptiste", "phone": "+50937004455", "course_id": course.id,
    })
    assert r.status_code == 201, r.content

    admin = _admin()
    # 1) L'inscription apparaît avec membre + téléphone + cours + montant.
    data = admin.get("/dashboard/api/enrollments/").json()
    assert data["total"] == 1
    row = data["items"][0]
    assert row["member"]["phone"] == "+50937004455"
    assert row["course"]["title"] == "Gestion d'épargne"
    assert row["course"]["price_htg"] == 2000

    # 2) Recherche synchronisée (nom / téléphone / cours).
    assert admin.get("/dashboard/api/enrollments/?search=Baptiste").json()["total"] == 1
    assert admin.get("/dashboard/api/enrollments/?search=zzzzz").json()["total"] == 0

    # 3) Stats pipeline : 1 en attente, CA confirmé = 0 tant que non confirmé.
    stats = admin.get("/dashboard/api/enrollments/?stats=1").json()["stats"]
    assert stats["total"] == 1 and stats["pending"] == 1
    assert stats["confirmed"] == 0 and stats["confirmed_revenue"] == 0

    # 4) Confirmation admin -> le CA confirmé suit le prix du cours.
    eid = Enrollment.objects.get().id
    assert admin.put(f"/dashboard/api/enrollments/{eid}/",
                     data=json.dumps({"status": "confirmed"}),
                     content_type="application/json").status_code == 200
    stats2 = admin.get("/dashboard/api/enrollments/?stats=1").json()["stats"]
    assert stats2["confirmed"] == 1 and stats2["confirmed_revenue"] == 2000


# ─────────────────────────── RÉSERVATION ───────────────────────────
def _slot_occupied(client, date, slot="matin"):
    av = client.get(f"/api/venue-availability/?from={date}&to={date}").json()
    return slot in (av.get("occupied", {}).get(date, []))


def test_booking_site_to_admin_sync_and_availability():
    pub = Client()
    r = _post(pub, "/api/venue-bookings/", {
        "requester_name": "Paul Joseph", "requester_phone": "+50934009988",
        "event_type": "Mariage", "event_date": FUTURE,
        "start_time": "08:00", "end_time": "12:00", "setup": "assis 40", "guest_count": 40,
    })
    assert r.status_code == 201, r.content

    admin = _admin()
    # 1) La réservation apparaît dans l'admin.
    data = admin.get("/dashboard/api/bookings/").json()
    assert data["total"] == 1
    bk = data["items"][0]
    assert bk["requester_name"] == "Paul Joseph"
    bid = bk["id"]

    # 2) Une demande fraîche (statut « requested ») n'occupe pas encore la date.
    assert _slot_occupied(pub, FUTURE) is False

    # 3) L'admin confirme -> la date devient occupée côté site.
    assert admin.put(f"/dashboard/api/bookings/{bid}/",
                     data=json.dumps({"status": "confirmed"}),
                     content_type="application/json").status_code == 200
    assert _slot_occupied(pub, FUTURE) is True

    # 4) Le bouton « Réinitialiser » (annule tout) -> la date est de nouveau libre.
    rr = admin.post("/dashboard/api/bookings/reset/",
                    data=json.dumps({"confirm": True}), content_type="application/json")
    assert rr.status_code == 200 and rr.json()["cancelled"] >= 1
    assert VenueBooking.objects.get(id=bid).status == "cancelled"
    assert _slot_occupied(pub, FUTURE) is False


# ─────────────────── Isolation RBAC des 3 sections ───────────────────
def test_gestion_sections_require_their_own_access():
    """Un admin délégué ne voit que les sections de gestion qui lui sont attribuées."""
    from apps.adminpanel.models import AdminAccess
    u = User.objects.create_user("deleg_sync", "d_sync@x.com", "password123")
    u.is_staff = True
    u.save()
    AdminAccess.objects.create(user=u, sections=["contacts"])  # contacts seulement
    c = Client()
    c.force_login(u)
    assert c.get("/dashboard/api/contacts/").status_code == 200       # autorisé
    assert c.get("/dashboard/api/enrollments/").status_code == 403    # refusé
    assert c.get("/dashboard/api/bookings/").status_code == 403       # refusé

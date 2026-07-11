"""Regressions de robustesse backend (audit multi-agents, sprint 1).

Verifie qu'un corps JSON non-objet, une valeur hors-bornes ou une date invalide
renvoient 400 et JAMAIS 500, et que le filtre produits ne masque plus les actifs.
"""
import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.adminpanel.models import AdminNotification, AuditLog, GEI, Product

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


# ── Notifications : « Tout effacer » vide vraiment le panneau ─────────────
def test_notifications_clear_empties_panel_and_badge():
    for i in range(4):
        AdminNotification.objects.create(message=f"N{i}", notification_type="new_booking", is_read=(i < 1))
    c = _admin()
    assert c.get("/dashboard/api/notifications/check/").json()["unread_count"] == 3
    # scope=read ne retire que les lues
    c.post("/dashboard/api/notifications/clear/?scope=read")
    assert AdminNotification.objects.count() == 3
    # tout effacer -> panneau vide + badge 0
    r = c.post("/dashboard/api/notifications/clear/")
    assert r.status_code == 200
    assert AdminNotification.objects.count() == 0
    assert c.get("/dashboard/api/notifications/").json() == []
    assert c.get("/dashboard/api/notifications/check/").json()["unread_count"] == 0


# ── B-3 : matérialisation du CA formation idempotente (get_or_create) ─────
def test_materialize_course_payment_idempotent():
    from apps.adminpanel.models import Course, CourseEnrollment, Payment
    from apps.adminpanel.views import _materialize_course_payment
    course = Course.objects.create(title="Cours payant", category="F", instructor="P", city="V", price_htg=1500)
    student = User.objects.create_user("etu1", "e1@x.com", "password123")
    enr = CourseEnrollment.objects.create(student=student, course=course,
                                          status=CourseEnrollment.Status.ACTIVE)
    _materialize_course_payment(enr)
    _materialize_course_payment(enr)  # 2e appel (TOCTOU) -> ne doit PAS créer un doublon
    assert Payment.objects.filter(external_reference=f"CE-{enr.pk}").count() == 1


# ── B-6 : traçabilité des actions sensibles (AuditLog explicite) ─────────
def test_sensitive_actions_are_audited():
    c = _admin()
    # suppression de masse -> une entrée d'audit "delete"
    GEI.objects.create(name="GEI X", city="PAP")
    AuditLog.objects.all().delete()
    c.post("/dashboard/api/bulk-delete/geis/",
           data=json.dumps({"confirm": "SUPPRIMER"}), content_type="application/json")
    assert AuditLog.objects.filter(action="delete", model_name="geis").exists()

    # réinitialisation du calendrier -> audit "update"
    AuditLog.objects.all().delete()
    c.post("/dashboard/api/bookings/reset/", data=json.dumps({"confirm": True}),
           content_type="application/json")
    assert AuditLog.objects.filter(action="update", model_name="VenueBooking").exists()

    # changement de mot de passe self-service -> audit "update" sur Admin
    AuditLog.objects.all().delete()
    c.post("/dashboard/api/account/password/",
           data=json.dumps({"current_password": "password123", "new_password": "NouveauFort456!"}),
           content_type="application/json")
    assert AuditLog.objects.filter(action="update", model_name="Admin").exists()


# ── B-9 : un prof NON approuvé ne peut pas gérer ses cours ────────────────
def test_unapproved_teacher_cannot_manage():
    from apps.adminpanel.models import Course, Profile
    from apps.formation.views import _can_manage
    teacher = User.objects.create_user("prof1", "p1@x.com", "password123")
    prof = Profile.objects.create(user=teacher, role=Profile.Role.TEACHER, is_approved=False)
    course = Course.objects.create(title="C", category="F", instructor="P", city="V", teacher=teacher)
    assert _can_manage(teacher, course) is False  # non approuvé -> refusé
    prof.is_approved = True
    prof.save()
    assert _can_manage(teacher, course) is True   # approuvé -> autorisé


# ── B-8 : le compteur d'étudiants formation (LMS) est distinct des inscriptions mutuelle
def test_course_exposes_student_enrollment_count():
    from apps.adminpanel.models import Course, CourseEnrollment, Enrollment, Member
    course = Course.objects.create(title="Cours LMS", category="F", instructor="P", city="V", price_htg=0)
    # 1 étudiant LMS + 1 inscription mutuelle -> comptés séparément
    student = User.objects.create_user("etu2", "e2@x.com", "password123")
    CourseEnrollment.objects.create(student=student, course=course)
    Enrollment.objects.create(member=Member.objects.create(first_name="A", last_name="B", phone="509"), course=course)
    d = _admin().get("/dashboard/api/courses/").json()
    row = next(c for c in d["items"] if c["id"] == course.id)
    assert row["student_enrollment_count"] == 1
    assert row["enrollment_count"] == 1


# ── B-10 : logout formation en GET -> 405 (POST uniquement) ───────────────
def test_formation_logout_get_not_allowed():
    r = Client().get("/formation/deconnexion/")
    assert r.status_code == 405


# ── B-2 : suivi de stock OPT-IN par produit ──────────────────────────────
def _order(pid, qty):
    return Client().post("/api/orders/", data=json.dumps({
        "customer_name": "Cli", "customer_phone": "509", "delivery_address": "Rue X",
        "items": [{"product_id": pid, "quantity": qty}],
    }), content_type="application/json")


def test_stock_tracking_optin():
    # Produit SUIVI : commande au-delà du stock -> refusée (409) ; dans la limite -> OK
    tracked = Product.objects.create(name="Suivi", price_htg=500, stock=2, track_stock=True)
    assert _order(tracked.id, 3).status_code == 409
    assert _order(tracked.id, 2).status_code == 201
    # Produit NON suivi (défaut, stock=0) : aucune limite -> commande acceptée
    untracked = Product.objects.create(name="NonSuivi", price_htg=500, stock=0, track_stock=False)
    assert _order(untracked.id, 5).status_code == 201


# ── A-8 : agrégations optimisées -> valeurs correctes (aucun chiffre changé) ─
def test_a8_overview_aggregations_correct():
    from apps.adminpanel.models import Course, CourseEnrollment
    c = _admin()
    GEI.objects.all().delete()
    GEI.objects.create(name="G1", city="PAP", is_active=True)
    GEI.objects.create(name="G2", city="PAP", is_active=False)
    gstats = c.get("/dashboard/api/geis/overview/").json()["stats"]
    assert gstats["total"] == 2 and gstats["active"] == 1 and gstats["inactive"] == 1

    Course.objects.all().delete()
    co1 = Course.objects.create(title="C1", category="Fin", instructor="P", city="V", is_active=True, price_htg=1000)
    Course.objects.create(title="C2", category="Ges", instructor="P", city="V", is_active=False, price_htg=500)
    stu = User.objects.create_user("stuB", "sb@x.com", "password123")
    CourseEnrollment.objects.create(student=stu, course=co1, status=CourseEnrollment.Status.ACTIVE)
    cstats = c.get("/dashboard/api/courses/overview/").json()
    assert cstats["stats"]["total"] == 2 and cstats["stats"]["active"] == 1
    assert cstats["stats"]["students"] == 1 and cstats["stats"]["active_access"] == 1
    assert cstats["stats"]["revenue_confirmed"] == 1000
    assert cstats["categories"] == ["Fin", "Ges"]


def test_a8_revenue_buckets_by_calendar_month():
    from datetime import timedelta
    from django.utils import timezone
    from apps.adminpanel.models import Payment
    from apps.adminpanel.views import _serialize_revenue_for_react
    now = timezone.now()
    Payment.objects.create(purpose="course", status=Payment.Status.PAID, payer_name="X", amount_htg=700)
    Payment.objects.create(purpose="course", status=Payment.Status.PAID, payer_name="Y", amount_htg=300)
    p = Payment.objects.create(purpose="course", status=Payment.Status.PAID, payer_name="Z", amount_htg=400)
    Payment.objects.filter(pk=p.pk).update(created_at=now.replace(day=1) - timedelta(days=1))
    rev = _serialize_revenue_for_react()
    assert len(rev) == 6
    assert rev[-1]["v"] == 1000   # mois courant (700+300)
    assert rev[-2]["v"] == 400    # mois précédent


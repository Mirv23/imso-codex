"""Tests des correctifs de sécurité du panneau admin (A1, A3, A4, A5, A6)."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, override_settings
from django.urls import reverse

from .models import AuditLog, Course, Enrollment, GEI, Member, Payment, PaymentProvider

User = get_user_model()


def _staff(client):
    user = User.objects.create_superuser("boss", "boss@test.com", "password123")
    client.force_login(user)
    return user


def _regular(client):
    # Simule un futur compte client de la boutique : authentifié mais NON staff.
    user = User.objects.create_user("client1", "client@test.com", "password123")
    client.force_login(user)
    return user


# ── A1 : séparation admin / client ───────────────────────────────

@pytest.mark.django_db
class TestStaffSeparation:
    def test_non_staff_forbidden_v1(self):
        client = Client()
        _regular(client)
        response = client.get(reverse("adminpanel:member-list"))
        assert response.status_code == 403

    def test_non_staff_forbidden_v2(self):
        client = Client()
        _regular(client)
        response = client.get("/dashboard/api/v2/members/")
        assert response.status_code == 403

    def test_non_staff_dashboard_redirects_to_login(self):
        # Un non-staff connecté (ex. étudiant/prof de la plateforme formation,
        # session partagée) est redirigé vers la connexion admin plutôt que de
        # recevoir un 403 sec, pour pouvoir se reconnecter en administrateur.
        client = Client()
        _regular(client)
        response = client.get(reverse("adminpanel:dashboard"))
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    def test_staff_allowed(self):
        client = Client()
        _staff(client)
        assert client.get(reverse("adminpanel:member-list")).status_code == 200
        assert client.get("/dashboard/api/v2/members/").status_code == 200


# ── A4 : l'export CSV ne fuit pas les secrets ────────────────────

@pytest.mark.django_db
class TestCsvExportSecrets:
    def test_provider_export_excludes_secret_key(self):
        PaymentProvider.objects.create(
            name="MonCash IMSO",
            provider_type=PaymentProvider.ProviderType.MONCASH,
            api_secret_key="TOPSECRET-XYZ-123",
        )
        client = Client()
        _staff(client)
        response = client.get(reverse("adminpanel:export-csv", args=["providers"]))
        content = b"".join(response.streaming_content).decode("utf-8")
        assert "api_secret_key" not in content
        assert "TOPSECRET-XYZ-123" not in content


# ── A5 : garde-fous de suppression ───────────────────────────────

@pytest.mark.django_db
class TestDeletionGuards:
    def test_delete_member_with_enrollment_cascades(self):
        # Un membre est supprimable quel que soit son statut / ses inscriptions
        # (demande explicite). Les inscriptions sont supprimées en cascade.
        gei = GEI.objects.create(name="GEI A", city="PAP")
        member = Member.objects.create(first_name="Jean", last_name="Pierre", phone="509", gei=gei)
        course = Course.objects.create(title="Compta", category="Gestion", instructor="X", city="PAP")
        enrollment = Enrollment.objects.create(member=member, course=course)
        client = Client()
        _staff(client)
        response = client.delete(reverse("adminpanel:member-detail", args=[member.pk]))
        assert response.status_code == 200
        assert not Member.objects.filter(pk=member.pk).exists()
        assert not Enrollment.objects.filter(pk=enrollment.pk).exists()

    def test_delete_member_without_links_ok(self):
        member = Member.objects.create(first_name="Marie", last_name="Jean", phone="509")
        client = Client()
        _staff(client)
        response = client.delete(reverse("adminpanel:member-detail", args=[member.pk]))
        assert response.status_code == 200
        assert not Member.objects.filter(pk=member.pk).exists()


# ── A6 : journal d'audit ─────────────────────────────────────────

@pytest.mark.django_db
class TestAuditLog:
    def test_staff_create_is_audited(self):
        client = Client()
        _staff(client)
        client.post(
            reverse("adminpanel:gei-create"),
            data={"name": "GEI Nord", "city": "Cap-Haïtien"},
            content_type="application/json",
        )
        assert AuditLog.objects.filter(action="create", model_name="GEI").exists()
        entry = AuditLog.objects.get(action="create", model_name="GEI")
        assert entry.username == "boss"

    def test_public_creation_not_audited(self):
        # Une soumission publique (visiteur anonyme) ne doit pas générer d'audit.
        client = Client()
        client.post(
            reverse("core:contact_request_create"),
            data={"full_name": "Anon", "phone": "509", "subject": "membership"},
            content_type="application/json",
        )
        assert not AuditLog.objects.filter(model_name="ContactRequest").exists()


# ── A3 : rate-limit du login ─────────────────────────────────────

@pytest.mark.django_db
class TestLoginRateLimit:
    # Cache isolé pour ce test : le rate-limiting utilise désormais le cache
    # "ratelimit" (RATELIMIT_USE_CACHE) — on l'isole en LocMem dédié pour éviter
    # toute contamination du compteur entre tests et ne pas dépendre de la table DB.
    @override_settings(
        RATELIMIT_USE_CACHE="ratelimit",
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "default-isolated",
            },
            "ratelimit": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "ratelimit-login-isolated",
            },
        },
    )
    def test_login_brute_force_blocked(self):
        caches["ratelimit"].clear()
        client = Client()
        statuses = []
        for _ in range(8):
            resp = client.post(reverse("login"), {"username": "boss", "password": "wrong"})
            statuses.append(resp.status_code)
        # Au-delà du seuil (5/min par identifiant), la vue renvoie 403 (Ratelimited).
        assert 403 in statuses


# ── Permissions par section (admin simple vs super-admin) ────────

@pytest.mark.django_db
class TestSectionPermissions:
    def _limited(self, sections):
        from .models import AdminAccess
        u = User.objects.create_user("agent1", "a@test.com", "password123", is_staff=True)
        AdminAccess.objects.create(user=u, sections=sections, note="test")
        c = Client()
        c.force_login(u)
        return c

    def test_limited_admin_only_sees_granted_sections(self):
        client = self._limited(["members", "payments"])
        # Autorisé
        assert client.get(reverse("adminpanel:member-list")).status_code == 200
        assert client.get(reverse("adminpanel:payment-list")).status_code == 200
        # Refusé (section non attribuée) → 403
        assert client.get(reverse("adminpanel:course-list")).status_code == 403
        assert client.get(reverse("adminpanel:blog-list")).status_code == 403
        # Coquille du dashboard toujours accessible
        assert client.get(reverse("adminpanel:summary")).status_code == 200
        assert client.get(reverse("adminpanel:charts")).status_code == 200

    def test_limited_admin_cannot_reach_admins_section(self):
        client = self._limited(["members"])
        # La gestion des admins est réservée aux super-administrateurs.
        assert client.get(reverse("adminpanel:admin-list")).status_code == 403

    def test_limited_admin_write_blocked_outside_scope(self):
        client = self._limited(["members"])
        import json
        r = client.post(reverse("adminpanel:course-create"),
                        data=json.dumps({"title": "X", "category": "Y", "instructor": "Z", "city": "PAP"}),
                        content_type="application/json")
        assert r.status_code == 403

    def test_superuser_sees_everything(self):
        client = Client()
        _staff(client)  # crée un superuser
        for name in ("member-list", "course-list", "blog-list", "admin-list", "settings-detail"):
            assert client.get(reverse(f"adminpanel:{name}")).status_code == 200

    def test_superadmin_assigns_sections_on_create(self):
        import json
        client = Client()
        _staff(client)
        r = client.post(reverse("adminpanel:admin-create"),
                        data=json.dumps({"username": "agent2", "password": "password123",
                                         "sections": ["members", "geis"], "note": "GEIs"}),
                        content_type="application/json")
        assert r.status_code == 201
        assert set(r.json()["sections"]) == {"members", "geis"}

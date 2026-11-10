"""Page publique d'inscription a la formation (/register/) et sa section admin."""

import datetime
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client

from apps.adminpanel.models import AdminNotification, SiteSetting, TrainingRegistration
from apps.core.training import CURRENT_TRAINING

User = get_user_model()

VALID = {
    "first_name": "  Jean  ",
    "last_name": "Pierre",
    "phone": "+509 33 70 7662",
    "status": "entrepreneur",
    "status_other": "",
    "age_range": "25_34",
    "interests": "Faire un budget pour mon commerce.",
}


@pytest.fixture(autouse=True)
def _clear_ratelimit():
    caches["ratelimit"].clear()


@pytest.mark.django_db
class TestRegisterPage:
    def test_page_renders_the_training_and_the_form(self):
        resp = Client().get("/register/")
        assert resp.status_code == 200
        html = resp.content.decode()
        assert CURRENT_TRAINING["title"] in html
        assert "45, rue Général Borgella, Les Cayes" in html
        for name in ("first_name", "last_name", "phone", "status", "status_other", "age_range", "interests"):
            assert f'name="{name}"' in html
        # L'age exact n'est jamais demande : seulement un curseur de tranches.
        assert 'type="range"' in html

    def test_flyer_address_without_slash_redirects(self):
        resp = Client().get("/register")
        assert resp.status_code in (301, 302)
        assert resp["Location"].endswith("/register/")

    def test_valid_submission_is_saved_and_thanked(self):
        client = Client()
        resp = client.post("/register/", VALID)
        assert resp.status_code == 302
        assert resp["Location"].endswith("/register/merci/")
        r = TrainingRegistration.objects.get()
        assert r.event == CURRENT_TRAINING["slug"]
        assert r.first_name == "Jean"
        assert r.status == "entrepreneur" and r.age_range == "25_34"
        assert AdminNotification.objects.filter(related_id=r.pk).exists()
        done = client.get(resp["Location"])
        assert "Merci Jean" in done.content.decode()

    def test_age_range_is_required(self):
        resp = Client().post("/register/", {**VALID, "age_range": ""})
        assert resp.status_code == 200
        assert "tranche d&#x27;âge" in resp.content.decode()
        assert not TrainingRegistration.objects.exists()

    def test_other_status_needs_a_precision(self):
        resp = Client().post("/register/", {**VALID, "status": "autre", "status_other": " "})
        assert "Précisez votre statut" in resp.content.decode()
        assert not TrainingRegistration.objects.exists()
        Client().post("/register/", {**VALID, "status": "autre", "status_other": "Commerçante"})
        assert TrainingRegistration.objects.get().status_label == "Commerçante"

    def test_same_phone_cannot_register_twice(self):
        Client().post("/register/", VALID)
        resp = Client().post("/register/", {**VALID, "phone": "33707662"})
        assert "déjà inscrit" in resp.content.decode()
        assert TrainingRegistration.objects.count() == 1

    def test_invalid_phone_is_rejected(self):
        resp = Client().post("/register/", {**VALID, "phone": "abc"})
        assert "ne semble pas valide" in resp.content.decode()
        assert not TrainingRegistration.objects.exists()

    def test_honeypot_saves_nothing(self):
        resp = Client().post("/register/", {**VALID, "website": "http://spam.example"})
        assert resp.status_code == 302
        assert not TrainingRegistration.objects.exists()

    def test_page_stays_open_during_maintenance(self):
        SiteSetting.objects.update_or_create(pk=1, defaults={"maintenance_mode": True})
        client = Client()
        assert client.get("/").status_code == 503
        assert client.get("/register/").status_code == 200
        assert client.post("/register/", VALID).status_code == 302
        assert TrainingRegistration.objects.count() == 1

    def test_registrations_close_after_the_last_day(self):
        after = CURRENT_TRAINING["last_day"] + datetime.timedelta(days=1)
        with mock.patch("apps.core.views.timezone.localdate", return_value=after):
            client = Client()
            assert "Inscriptions closes" in client.get("/register/").content.decode()
            client.post("/register/", VALID)
        assert not TrainingRegistration.objects.exists()


@pytest.mark.django_db
class TestRegistrationAdmin:
    def _admin(self):
        client = Client()
        client.force_login(User.objects.create_superuser("boss", "boss@t.com", "password123"))
        return client

    def test_anonymous_cannot_read_registrations(self):
        resp = Client().get("/dashboard/api/registrations/")
        assert resp.status_code in (302, 401, 403)

    def test_admin_lists_confirms_and_exports(self):
        Client().post("/register/", VALID)
        r = TrainingRegistration.objects.get()
        client = self._admin()

        data = client.get("/dashboard/api/registrations/?stats=1&status=entrepreneur").json()
        assert data["total"] == 1
        assert data["items"][0]["phone"] == "+509 33 70 7662"
        assert data["items"][0]["age_range_label"] == "25 – 34 ans"
        assert data["stats"]["by_status"]["entrepreneur"] == 1

        resp = client.put(f"/dashboard/api/registrations/{r.pk}/", data='{"is_confirmed": true}',
                          content_type="application/json")
        assert resp.status_code == 200
        r.refresh_from_db()
        assert r.is_confirmed

        csv = b"".join(client.get("/dashboard/api/export/registrations/").streaming_content).decode("utf-8")
        assert "Pierre" in csv and "33 70 7662" in csv

    def test_section_is_grantable_to_a_delegated_admin(self):
        from apps.adminpanel.sections import GRANTABLE_SECTIONS, section_for_urlname

        assert "registrations" in GRANTABLE_SECTIONS
        assert section_for_urlname("registration-list") == "registrations"
        assert section_for_urlname("registration-detail") == "registrations"

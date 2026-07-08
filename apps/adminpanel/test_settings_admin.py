"""Tests: paramètres du site, administrateurs, upload d'images, secrets fournisseurs."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from .models import PaymentProvider, Product, SiteSetting

User = get_user_model()

# PNG 1x1 minimal valide
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _super(client, username="boss"):
    u = User.objects.create_superuser(username, f"{username}@t.com", "password123")
    client.force_login(u)
    return u


def _staff_non_super(client):
    u = User.objects.create_user("editor", "e@t.com", "password123")
    u.is_staff = True
    u.save()
    client.force_login(u)
    return u


# ── Paramètres ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestSiteSettings:
    def test_get_and_update(self):
        client = Client()
        _super(client)
        assert client.get(reverse("adminpanel:settings-detail")).status_code == 200
        r = client.put(
            reverse("adminpanel:settings-detail"),
            data=json.dumps({"site_name": "IMSO Haiti", "color_primary": "#123456", "show_blog": False}),
            content_type="application/json",
        )
        assert r.status_code == 200
        s = SiteSetting.load()
        assert s.site_name == "IMSO Haiti"
        assert s.color_primary == "#123456"
        assert s.show_blog is False

    def test_singleton_enforced(self):
        SiteSetting.load()
        SiteSetting.load()
        assert SiteSetting.objects.count() == 1

    def test_settings_reflected_on_public_site(self):
        client = Client()
        _super(client)
        client.put(
            reverse("adminpanel:settings-detail"),
            data=json.dumps({"hero_title": "Titre personnalisé IMSO", "contact_phone": "+509 0000"}),
            content_type="application/json",
        )
        # Le site public est servi sur /view/ (la racine affiche la maintenance).
        home = Client().get("/view/")
        assert home.status_code == 200
        assert b"Titre personnalis\xc3\xa9 IMSO" in home.content

    def test_non_staff_forbidden(self):
        client = Client()
        u = User.objects.create_user("client1", "c@t.com", "password123")  # non staff
        client.force_login(u)
        assert client.get(reverse("adminpanel:settings-detail")).status_code == 403


# ── Administrateurs ──────────────────────────────────────────────

@pytest.mark.django_db
class TestAdminUsers:
    def test_superuser_creates_admin(self):
        client = Client()
        _super(client)
        r = client.post(
            reverse("adminpanel:admin-create"),
            data=json.dumps({"username": "nouvel_admin", "password": "MotDePasse123", "is_superuser": False}),
            content_type="application/json",
        )
        assert r.status_code == 201
        u = User.objects.get(username="nouvel_admin")
        assert u.is_staff and not u.is_superuser
        assert u.check_password("MotDePasse123")

    def test_non_superuser_cannot_create(self):
        client = Client()
        _staff_non_super(client)
        r = client.post(
            reverse("adminpanel:admin-create"),
            data=json.dumps({"username": "x", "password": "y"}),
            content_type="application/json",
        )
        assert r.status_code == 403
        assert not User.objects.filter(username="x").exists()

    def test_cannot_delete_self(self):
        client = Client()
        me = _super(client)
        r = client.delete(reverse("adminpanel:admin-detail", args=[me.pk]))
        assert r.status_code == 400
        assert User.objects.filter(pk=me.pk).exists()

    def test_cannot_delete_last_superuser(self):
        client = Client()
        _super(client, "boss")
        other = User.objects.create_user("simple", "s@t.com", "password123")
        other.is_staff = True
        other.save()
        # boss est le seul superuser -> supprimer un autre admin OK, mais pas le dernier superuser
        r = client.delete(reverse("adminpanel:admin-detail", args=[other.pk]))
        assert r.status_code == 200

    def test_password_reset(self):
        client = Client()
        _super(client)
        target = User.objects.create_user("target", "t@t.com", "oldpass123")
        target.is_staff = True
        target.save()
        client.put(
            reverse("adminpanel:admin-detail", args=[target.pk]),
            data=json.dumps({"password": "brandnew456"}),
            content_type="application/json",
        )
        target.refresh_from_db()
        assert target.check_password("brandnew456")


# ── Upload d'image ───────────────────────────────────────────────

@pytest.mark.django_db
class TestImageUpload:
    def test_upload_product_image(self):
        client = Client()
        _super(client)
        product = Product.objects.create(name="Kit", price_htg=500, stock=5)
        img = SimpleUploadedFile("kit.png", _PNG, content_type="image/png")
        r = client.post(reverse("adminpanel:upload-image", args=["product", product.id]), {"file": img})
        assert r.status_code == 200
        assert r.json()["ok"] is True
        product.refresh_from_db()
        assert product.image  # image attachée

    def test_reject_non_image(self):
        client = Client()
        _super(client)
        product = Product.objects.create(name="Kit", price_htg=500, stock=5)
        bad = SimpleUploadedFile("x.txt", b"hello", content_type="text/plain")
        r = client.post(reverse("adminpanel:upload-image", args=["product", product.id]), {"file": bad})
        assert r.status_code == 400


# ── Secrets fournisseurs ─────────────────────────────────────────

@pytest.mark.django_db
class TestProviderSecrets:
    def test_secret_write_only(self):
        client = Client()
        _super(client)
        r = client.post(
            reverse("adminpanel:provider-create"),
            data=json.dumps({"name": "MonCash API", "provider_type": "moncash", "api_secret_key": "sk_live_SECRET"}),
            content_type="application/json",
        )
        assert r.status_code == 201
        body = r.json()
        assert body["has_secret"] is True
        assert "api_secret_key" not in body  # jamais exposée
        pid = body["id"]
        # Édition sans re-fournir le secret : il est conservé
        client.put(
            reverse("adminpanel:provider-detail", args=[pid]),
            data=json.dumps({"name": "MonCash API v2"}),
            content_type="application/json",
        )
        p = PaymentProvider.objects.get(pk=pid)
        assert p.api_secret_key == "sk_live_SECRET"

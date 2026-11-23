# -*- coding: utf-8 -*-
"""JK-4 : libellé simplifié de la tuile « Femmes »."""
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.core.cache import cache

from apps.adminpanel.models import SiteSetting

migration = import_module("apps.adminpanel.migrations.0043_libelle_femmes_simplifie")


@pytest.fixture(autouse=True)
def _vide_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_libelle_remplace_s_il_est_au_texte_d_origine():
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women_label": migration.ANCIEN})
    migration.forwards(django_apps, None)
    assert SiteSetting.objects.get(pk=1).stat_women_label == migration.NOUVEAU


@pytest.mark.django_db
def test_retouche_admin_preservee():
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women_label": "Texte de l'admin"})
    migration.forwards(django_apps, None)
    assert SiteSetting.objects.get(pk=1).stat_women_label == "Texte de l'admin"


@pytest.mark.django_db
def test_accueil_affiche_le_nouveau_libelle(client):
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women_label": ""})
    html = client.get("/").content.decode()
    assert migration.NOUVEAU in html
    assert "fonds décaissés va aux entrepreneures" not in html

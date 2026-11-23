# -*- coding: utf-8 -*-
"""JK-4 : libellé simplifié de la tuile « Femmes »."""
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.core.cache import cache

from apps.adminpanel.models import SiteSetting

migration = import_module("apps.adminpanel.migrations.0043_libelle_femmes_simplifie")
migration_23 = import_module("apps.adminpanel.migrations.0044_libelle_femmes_23_pourcent")
migration_sans_titre = import_module("apps.adminpanel.migrations.0045_tuile_femmes_sans_titre")


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
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women": "", "stat_women_label": ""})
    html = client.get("/").content.decode()
    assert migration_sans_titre.NOUVEAU in html
    assert ">Femmes<" not in html
    assert "fonds décaissés va aux entrepreneures" not in html
    assert migration.NOUVEAU not in html


@pytest.mark.django_db
@pytest.mark.parametrize("ancien", [
    "Une large part des fonds décaissés va aux entrepreneures",
    "Une grande partie des fonds va aux femmes entrepreneures",
])
def test_libelle_23_pourcent_remplace_les_anciens_textes(ancien):
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women_label": ancien})
    migration_23.forwards(django_apps, None)
    assert SiteSetting.objects.get(pk=1).stat_women_label == "23% du montant décaissé aux femmes entrepreneures"


@pytest.mark.django_db
def test_libelle_23_pourcent_preserve_retouche_admin():
    SiteSetting.objects.update_or_create(pk=1, defaults={"stat_women_label": "Texte de l'admin"})
    migration_23.forwards(django_apps, None)
    assert SiteSetting.objects.get(pk=1).stat_women_label == "Texte de l'admin"


@pytest.mark.django_db
def test_tuile_femmes_sans_titre_et_nouvelle_description(client):
    SiteSetting.objects.update_or_create(pk=1, defaults={
        "stat_women": "Femmes", "stat_women_label": "23% du montant décaissé aux femmes entrepreneures"})
    migration_sans_titre.forwards(django_apps, None)
    s = SiteSetting.objects.get(pk=1)
    assert s.stat_women == ""
    assert s.stat_women_label == "23% du montant décaissé va aux femmes entrepreneures"
    html = client.get("/").content.decode()
    assert "23% du montant décaissé va aux femmes entrepreneures" in html
    assert ">Femmes<" not in html


@pytest.mark.django_db
def test_tuile_femmes_retouche_admin_preservee():
    SiteSetting.objects.update_or_create(pk=1, defaults={
        "stat_women": "Elles", "stat_women_label": "Texte de l'admin"})
    migration_sans_titre.forwards(django_apps, None)
    s = SiteSetting.objects.get(pk=1)
    assert (s.stat_women, s.stat_women_label) == ("Elles", "Texte de l'admin")

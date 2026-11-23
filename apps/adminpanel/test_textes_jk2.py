# -*- coding: utf-8 -*-
"""JK-2 : nom des GEI, chiffres de la mission, cours retirés, prix masqués."""
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.core.cache import cache

from apps.adminpanel.models import Course, ProcessStep, SiteSetting, SiteText

migration = import_module("apps.adminpanel.migrations.0041_textes_gei_chiffres_cours")


@pytest.fixture(autouse=True)
def _vide_cache():
    cache.clear()
    yield
    cache.clear()


def test_renomme_gei_singulier_et_pluriel():
    assert (
        migration.renomme_gei("Rejoindre un Groupe d'Entraide Intégrée")
        == "Rejoindre un Groupe d'Épargne et d'Investissement"
    )
    assert (
        migration.renomme_gei("au sein de Groupes d’Entraide Intégrée.")
        == "au sein de Groupes d'Épargne et d'Investissement."
    )
    assert migration.renomme_gei("Statuts du GEI") == "Statuts du GEI"
    assert migration.renomme_gei("") == ""


@pytest.mark.django_db
def test_migration_corrige_les_donnees():
    SiteSetting.objects.update_or_create(
        pk=1, defaults={"stat_repayment": "96%", "stat_repayment_label": "Taux de remboursement",
                        "hero_subtitle": "Au sein de Groupes d'Entraide Intégrée."},
    )
    SiteText.objects.update_or_create(
        key="cta_title", defaults={"label": "x", "value": "Rejoindre un Groupe d'Entraide Intégrée"}
    )
    SiteText.objects.update_or_create(
        key="why_card5_text", defaults={"label": "x", "value": "Texte retouché depuis l'admin."}
    )
    SiteText.objects.filter(key__in=["espace_cap1_num", "espace_cap2_num"]).delete()
    step = ProcessStep.objects.create(title="Étape", text="Groupe d'Entraide Intégrée local", sort_order=9)
    rh = Course.objects.create(title="Gestion RH", category="c", instructor="i", city="Les Cayes")
    tg = Course.objects.create(title="Techniques de gestion", category="c", instructor="i", city="Les Cayes")
    garde = Course.objects.create(title="Comptabilité de base", category="c", instructor="i", city="Les Cayes")

    migration.forwards(django_apps, None)

    s = SiteSetting.objects.get(pk=1)
    assert s.stat_savings == "8.6M"
    assert (s.stat_repayment, s.stat_repayment_label) == ("+100M", "HTG de projets financés")
    assert (s.stat_workshops, s.stat_workshops_label) == ("+800", "Projets approuvés")
    assert s.hero_subtitle == "Au sein de Groupes d'Épargne et d'Investissement."
    assert SiteText.objects.get(key="cta_title").value == "Rejoindre un Groupe d'Épargne et d'Investissement"
    # Une retouche faite depuis l'admin n'est pas écrasée.
    assert SiteText.objects.get(key="why_card5_text").value == "Texte retouché depuis l'admin."
    step.refresh_from_db()
    assert step.text == "Groupe d'Épargne et d'Investissement local"
    assert not Course.objects.get(pk=rh.pk).is_active
    assert not Course.objects.get(pk=tg.pk).is_active
    assert Course.objects.get(pk=garde.pk).is_active
    assert SiteText.objects.get(key="espace_cap1_num").value == "65+"
    assert SiteText.objects.get(key="espace_cap2_num").value == "50+"


@pytest.mark.django_db
def test_accueil_sans_prix_de_cours_et_avec_capacite_editable(client):
    SiteSetting.objects.update_or_create(pk=1, defaults={"show_courses": True, "maintenance_mode": False})
    Course.objects.create(title="Comptabilité de base", category="c", instructor="Jean",
                          city="Les Cayes", price_htg=2500, is_active=True)
    SiteText.objects.update_or_create(key="espace_cap1_num", defaults={"label": "x", "value": "75"})

    html = client.get("/").content.decode()

    assert "Comptabilité de base" in html
    assert '<div class="course-card__price">' not in html
    assert "Entraide Intégrée" not in html
    assert "Sans tables (75 personnes)" in html

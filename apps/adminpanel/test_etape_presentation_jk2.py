# -*- coding: utf-8 -*-
"""JK-2 (suite) : le badge « 1 jour » de l'étape « Présentation » disparaît."""
from importlib import import_module

import pytest
from django.apps import apps as django_apps
from django.core.cache import cache

from apps.adminpanel.models import ProcessStep, SiteSetting

migration = import_module("apps.adminpanel.migrations.0042_etape_presentation_sans_duree")


@pytest.mark.django_db
def test_badge_un_jour_retire_de_l_etape_presentation():
    presentation = ProcessStep.objects.create(
        title="Présentation", text="Présentation PowerPoint du modèle GEI", meta="⏱ 1 jour", sort_order=20)
    autre = ProcessStep.objects.create(title="Candidature", text="t", meta="⏱ 1 jour", sort_order=21)
    longue = ProcessStep.objects.create(title="Présentation", text="t", meta="⏱ 3 semaines", sort_order=22)

    migration.forwards(django_apps, None)

    assert ProcessStep.objects.get(pk=presentation.pk).meta == ""
    assert ProcessStep.objects.get(pk=autre.pk).meta == "⏱ 1 jour"
    assert ProcessStep.objects.get(pk=longue.pk).meta == "⏱ 3 semaines"


@pytest.mark.django_db
def test_accueil_sans_badge_un_jour_sur_la_presentation(client):
    cache.clear()
    SiteSetting.objects.update_or_create(pk=1, defaults={"maintenance_mode": False})
    ProcessStep.objects.create(
        title="Présentation", text="Présentation PowerPoint du modèle GEI", meta="⏱ 1 jour", sort_order=20)

    migration.forwards(django_apps, None)
    html = client.get("/").content.decode()
    cache.clear()

    assert "Présentation PowerPoint du modèle GEI" in html
    assert "⏱ 1 jour" not in html

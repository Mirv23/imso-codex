# -*- coding: utf-8 -*-
"""Rend éditables via « Textes du site » : le label « Notre mission » et l'icône
(emoji) de chacune des 4 puces de la section Mission. Les icônes sont semées
vides (valeur = "") : tant qu'elles restent vides, le template affiche la coche
par défaut ; renseigner un emoji dans l'admin le remplace. Idempotent."""
from django.db import migrations

SEED = [
    {"key": "mission_label", "label": "Label de la section Notre mission",
     "group": "Accueil - Mission", "value": "Notre mission"},
    {"key": "mission_icon_1", "label": "Icône puce mission 1 (emoji ; vide = coche)",
     "group": "Accueil - Mission", "value": ""},
    {"key": "mission_icon_2", "label": "Icône puce mission 2 (emoji ; vide = coche)",
     "group": "Accueil - Mission", "value": ""},
    {"key": "mission_icon_3", "label": "Icône puce mission 3 (emoji ; vide = coche)",
     "group": "Accueil - Mission", "value": ""},
    {"key": "mission_icon_4", "label": "Icône puce mission 4 (emoji ; vide = coche)",
     "group": "Accueil - Mission", "value": ""},
]


def seed(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    for e in SEED:
        SiteText.objects.get_or_create(
            key=e["key"],
            defaults={"label": e["label"], "group": e["group"], "value": e["value"]},
        )


def unseed(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    SiteText.objects.filter(key__in=[e["key"] for e in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0030_processstep_icon_processstep_image"),
    ]

    operations = [migrations.RunPython(seed, unseed)]

# -*- coding: utf-8 -*-
"""Seed des 3 clés SiteText de l'en-tête « Notre processus » (label/titre/intro),
rendues éditables comme la section jumelle « Nos valeurs ». Idempotent."""
from django.db import migrations

SEED = [
    {
        "key": "process_label",
        "label": "Label de la section Notre processus",
        "group": "Accueil - Processus",
        "value": "Notre processus",
    },
    {
        "key": "process_title",
        "label": "Titre de la section Notre processus",
        "group": "Accueil - Processus",
        "value": "Trois étapes simples pour rejoindre un GEI.",
    },
    {
        "key": "process_intro",
        "label": "Paragraphe d'introduction de la section Notre processus",
        "group": "Accueil - Processus",
        "value": "Un parcours pensé pour vous accueillir progressivement, le temps de "
                 "comprendre les règles communes et de bâtir des liens avec votre groupe.",
    },
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
        ("adminpanel", "0027_seed_values_steps_resync"),
    ]

    operations = [migrations.RunPython(seed, unseed)]

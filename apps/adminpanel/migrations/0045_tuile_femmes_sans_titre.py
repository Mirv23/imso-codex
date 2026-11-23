# -*- coding: utf-8 -*-
"""JK-4 (suite) : tuile « Femmes » de « Notre mission » sans grand titre.

Le grand titre « Femmes » est retiré (champ stat_women vidé ; le gabarit
n'affiche plus de titre quand ce champ est vide). La description devient
« 23% du montant décaissé va aux femmes entrepreneures ».

Les textes ne sont remplacés que s'ils sont encore à un texte posé par une
migration précédente : une retouche faite depuis l'admin est préservée.
"""
from django.db import migrations

TITRE = "Femmes"
ANCIENS = (
    "Une large part des fonds décaissés va aux entrepreneures",
    "Une grande partie des fonds va aux femmes entrepreneures",
    "23% du montant décaissé aux femmes entrepreneures",
)
NOUVEAU = "23% du montant décaissé va aux femmes entrepreneures"


def forwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women=TITRE).update(stat_women="")
    SiteSetting.objects.filter(stat_women_label__in=ANCIENS).update(stat_women_label=NOUVEAU)


def backwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women="").update(stat_women=TITRE)
    SiteSetting.objects.filter(stat_women_label=NOUVEAU).update(stat_women_label=ANCIENS[-1])


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0044_libelle_femmes_23_pourcent"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]

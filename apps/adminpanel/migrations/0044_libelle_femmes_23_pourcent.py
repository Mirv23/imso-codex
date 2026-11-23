# -*- coding: utf-8 -*-
"""JK-4 (suite) : la tuile « Femmes » de « Notre mission » affiche le chiffre.

Le libellé devient « 23% du montant décaissé aux femmes entrepreneures »
(demande de Mirv). Il n'est remplacé que s'il est encore à l'un des textes
posés par 0041 ou 0043 : une retouche faite depuis l'admin est préservée.
"""
from django.db import migrations

ANCIENS = (
    "Une large part des fonds décaissés va aux entrepreneures",
    "Une grande partie des fonds va aux femmes entrepreneures",
)
NOUVEAU = "23% du montant décaissé aux femmes entrepreneures"


def forwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women_label__in=ANCIENS).update(stat_women_label=NOUVEAU)


def backwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women_label=NOUVEAU).update(stat_women_label=ANCIENS[-1])


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0043_libelle_femmes_simplifie"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]

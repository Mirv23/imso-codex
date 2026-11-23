# -*- coding: utf-8 -*-
"""JK-4 : libellé plus simple pour la tuile « Femmes » de « Notre mission »
(section « Bâtir une économie solidaire portée par les communautés »).

« Une large part des fonds décaissés va aux entrepreneures » devient
« Une grande partie des fonds va aux femmes entrepreneures ».

Le texte n'est remplacé QUE s'il est encore au texte posé par 0041 : une
retouche faite depuis l'admin est préservée.
"""
from django.db import migrations

ANCIEN = "Une large part des fonds décaissés va aux entrepreneures"
NOUVEAU = "Une grande partie des fonds va aux femmes entrepreneures"


def forwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women_label=ANCIEN).update(stat_women_label=NOUVEAU)


def backwards(apps, schema_editor):
    SiteSetting = apps.get_model("adminpanel", "SiteSetting")
    SiteSetting.objects.filter(stat_women_label=NOUVEAU).update(stat_women_label=ANCIEN)


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0042_etape_presentation_sans_duree"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]

# -*- coding: utf-8 -*-
"""JK-2 (suite) : retirer le badge « 1 jour » de l'étape « Présentation ».

La migration 0041 ne cherchait « PowerPoint » que dans le titre de l'étape.
Sur le site, l'étape s'appelle « Présentation » et c'est son texte qui parle
de la « Présentation PowerPoint du modèle GEI » : le badge est donc resté.

Ici, on vide la durée (champ meta) d'une étape dont le titre commence par
« Présentation » ou dont le titre ou le texte mentionne PowerPoint, et
seulement si cette durée vaut « 1 jour » (avec ou sans pictogramme). Les
autres étapes et les autres durées ne bougent pas.
"""
import re

from django.db import migrations

POWERPOINT = re.compile(r"power\s*-?\s*point", re.IGNORECASE)
TITRE_PRESENTATION = re.compile(r"^\W*pr[ée]sentation\b", re.IGNORECASE)
DUREE_UN_JOUR = re.compile(r"^\W*(1|un)\s*(jour|journ[ée]e|j)\W*$", re.IGNORECASE)


def est_etape_presentation(title, text):
    title, text = title or "", text or ""
    return bool(TITRE_PRESENTATION.search(title) or POWERPOINT.search(title) or POWERPOINT.search(text))


def forwards(apps, schema_editor):
    ProcessStep = apps.get_model("adminpanel", "ProcessStep")
    for step in ProcessStep.objects.all():
        if est_etape_presentation(step.title, step.text) and DUREE_UN_JOUR.match(step.meta or ""):
            ProcessStep.objects.filter(pk=step.pk).update(meta="")


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0041_textes_gei_chiffres_cours"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

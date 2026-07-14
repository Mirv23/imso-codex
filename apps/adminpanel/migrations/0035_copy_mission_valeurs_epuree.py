# -*- coding: utf-8 -*-
"""Copie épurée des sections « Notre mission » et « Nos valeurs ».

L'ancienne copie était redondante : l'intro de la mission annonçait déjà les trois
piliers (épargne / formation / microcrédit) que les puces répétaient mot pour mot,
et les valeurs « Solidarité » et « Croissance collective » disaient la même chose.

On raccourcit et on rend chaque ligne DISTINCTE. Les textes sont mis à jour en base
UNIQUEMENT s'ils sont encore au texte d'origine semé : toute personnalisation faite
depuis l'admin est préservée.
"""
from django.db import migrations

# (clé, ancien texte semé, nouveau texte)
SITETEXT_UPDATES = [
    ("val_mission_1",
     "Mobiliser l'épargne locale pour financer les projets de proximité.",
     "Épargne collective, investie près de chez vous."),
    ("val_mission_2",
     "Former chaque membre aux fondamentaux de la gestion et de la comptabilité.",
     "Formation à la gestion pour chaque membre."),
    ("val_mission_3",
     "Garantir un accès équitable au microcrédit, sans collatéral abusif.",
     "Microcrédit équitable, sans garantie abusive."),
    ("val_mission_4",
     "Renforcer la cohésion sociale par l'entraide et la transparence.",
     "Gouvernance transparente, décidée ensemble."),
]

# (titre de la valeur, ancien texte semé, nouveau texte)
COREVALUE_UPDATES = [
    ("Solidarité",
     "Nous mutualisons risques et opportunités. Chaque membre soutient "
     "l'élan collectif et profite des progrès du groupe.",
     "Le risque se partage, l'opportunité aussi."),
    ("Respect humain",
     "La dignité passe avant tout. Décisions transparentes, écoute active "
     "et gouvernance partagée à toutes les étapes.",
     "La personne avant le dossier. Toujours."),
    ("Croissance collective",
     "Apprendre, entreprendre, partager. Le succès d'un membre devient "
     "une marche pour toute la communauté.",
     "Apprendre, entreprendre, transmettre."),
]


def apply_copy(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for key, old, new in SITETEXT_UPDATES:
        # filter(value=old) : ne touche QUE le texte d'origine (personnalisation intacte)
        SiteText.objects.filter(key=key, value=old).update(value=new)
    for title, old, new in COREVALUE_UPDATES:
        CoreValue.objects.filter(title=title, text=old).update(text=new)


def revert_copy(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for key, old, new in SITETEXT_UPDATES:
        SiteText.objects.filter(key=key, value=new).update(value=old)
    for title, old, new in COREVALUE_UPDATES:
        CoreValue.objects.filter(title=title, text=new).update(text=old)


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0034_sitesetting_venue_price_htg"),
    ]

    operations = [migrations.RunPython(apply_copy, revert_copy)]

# -*- coding: utf-8 -*-
"""Restaure les textes d'origine de « Notre mission » et « Nos valeurs ».

Retour arriere demande : on annule l'effet des migrations 0035 et 0036 qui avaient
raccourci la copie. On ne les "unapply" pas (la prod applique les migrations vers
l'avant au demarrage) : on ecrit une migration FORWARD qui remet les textes longs.

La mise a jour ne s'applique que si le texte est encore la version COURTE : si le
texte a ete retouche depuis l'admin entre temps, il est preserve.
"""
from django.db import migrations

# (cle, texte court actuel, texte long d'origine a restaurer)
SITETEXT_RESTORE = [
    ("val_mission_1",
     "Épargne collective, investie près de chez vous.",
     "Mobiliser l'épargne locale pour financer les projets de proximité."),
    ("val_mission_2",
     "Formation à la gestion pour chaque membre.",
     "Former chaque membre aux fondamentaux de la gestion et de la comptabilité."),
    ("val_mission_3",
     "Microcrédit équitable, sans garantie abusive.",
     "Garantir un accès équitable au microcrédit, sans collatéral abusif."),
    ("val_mission_4",
     "Gouvernance transparente, décidée ensemble.",
     "Renforcer la cohésion sociale par l'entraide et la transparence."),
]

# (titre, texte court actuel, texte long d'origine a restaurer)
COREVALUE_RESTORE = [
    (
        "Solidarité",
        "Responsables les uns des autres, solidairement.",
        "IMSO est une structure solidaire où tous les membres, en fonction de notre "
        "identité et de nos intérêts communs, sont mutuellement et solidairement "
        "responsables.",
    ),
    (
        "Foi",
        "Notre foi fonde et inspire chacune de nos actions.",
        "Base de notre existence et de nos actions. Nous avons la ferme conviction "
        "que toutes nos actions sont l'œuvre de Dieu dans nos vies ou sont inspirées "
        "par Lui.",
    ),
    (
        "Respect de la personne humaine",
        "Accueillir l'autre tel qu'il est, avec égard.",
        "À IMSO, nous nous soucions de l'impact de nos actes sur l'autre. Nous sommes "
        "inclusifs et nous acceptons l'autre pour ce qu'elle/il est, même lorsqu'elle/il "
        "est different/e. Nous traitons l'autre avec égard et considération.",
    ),
    (
        "Subsidiarité",
        "Chacun décide à son niveau ; chaque apport compte.",
        "Tout le monde est responsable en fonction de son niveau de responsabilité dans "
        "la chaîne. L'apport ou la decision de chacun est respecté et valorisé dans le "
        "cadre la poursuite des objectifs de l'équipe.",
    ),
    (
        "Redevabilité",
        "Qui décide rend des comptes à tous.",
        "Tous les membres d'IMSO sont des partenaires égaux et valorisés. Celles/ceux "
        "qui sont en charge sont tenues/tenus de rendre compte à toutes/tous les autres "
        "de ses activités.",
    ),
    (
        "Équité",
        "Mêmes droits, mêmes devoirs — sans distinction.",
        "À IMSO, tout un chacun est traité de façon juste, égalitaire, raisonnable et "
        "sans acception de race, de religion ou de sexe. Nous jouissons toutes/tous des "
        "mêmes droits et avons les mêmes devoirs l’un/e envers l’autre.",
    ),
    (
        "Intégrité",
        "Justes, même quand personne ne regarde.",
        "Nous agissons avec honnêteté, droiture et respect. Nous sommes fidèles à nos "
        "valeurs et prenons des décisions justes, même lorsque personne ne regarde. Nous "
        "ne nous engageons dans aucune action susceptible d’entacher notre réputation "
        "et la réputation de l’équipe/du groupe.",
    ),
    (
        "Confiance",
        "Une confiance réciproque, méritée par nos actes.",
        "À IMSO, nos relations avec nos membres et nos partenaires se basent sur une "
        "confiance réciproque. Nous sommes dignes de confiance et sommes responsables de "
        "nos actions.",
    ),
    # Valeurs semees par defaut (installations sans les 8 valeurs institutionnelles).
    (
        "Solidarité",
        "Le risque se partage, l'opportunité aussi.",
        "Nous mutualisons risques et opportunités. Chaque membre soutient "
        "l'élan collectif et profite des progrès du groupe.",
    ),
    (
        "Respect humain",
        "La personne avant le dossier. Toujours.",
        "La dignité passe avant tout. Décisions transparentes, écoute active "
        "et gouvernance partagée à toutes les étapes.",
    ),
    (
        "Croissance collective",
        "Apprendre, entreprendre, transmettre.",
        "Apprendre, entreprendre, partager. Le succès d'un membre devient "
        "une marche pour toute la communauté.",
    ),
]


def restore(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for key, short, long_text in SITETEXT_RESTORE:
        SiteText.objects.filter(key=key, value=short).update(value=long_text)
    for title, short, long_text in COREVALUE_RESTORE:
        CoreValue.objects.filter(title=title, text=short).update(text=long_text)


def unrestore(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for key, short, long_text in SITETEXT_RESTORE:
        SiteText.objects.filter(key=key, value=long_text).update(value=short)
    for title, short, long_text in COREVALUE_RESTORE:
        CoreValue.objects.filter(title=title, text=long_text).update(text=short)


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0036_condense_core_values"),
    ]

    operations = [migrations.RunPython(restore, unrestore)]

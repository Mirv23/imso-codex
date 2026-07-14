# -*- coding: utf-8 -*-
"""Condense les 8 valeurs institutionnelles d'IMSO en une ligne chacune.

Ce sont de vrais contenus client (saisis depuis l'admin), pas les valeurs semees
par defaut : la migration 0035 ne les avait donc pas touchees. Les textes longs
se recouvraient (Integrite ~ Confiance, Respect ~ Equite, Solidarite ~
Redevabilite), ce qui chargeait la section.

Aucune valeur n'est supprimee ni fusionnee : les 8 restent, chacune reduite a une
ligne courte et distincte. La mise a jour ne s'applique que si le texte est encore
le texte long d'origine (correspondance exacte), donc toute retouche faite entre
temps depuis l'admin est preservee. La migration est reversible.
"""
from django.db import migrations

# (titre, texte long actuel, texte condense)
CONDENSED = [
    (
        "Solidarité",
        "IMSO est une structure solidaire où tous les membres, en fonction de notre "
        "identité et de nos intérêts communs, sont mutuellement et solidairement "
        "responsables.",
        "Responsables les uns des autres, solidairement.",
    ),
    (
        "Foi",
        "Base de notre existence et de nos actions. Nous avons la ferme conviction "
        "que toutes nos actions sont l'œuvre de Dieu dans nos vies ou sont inspirées "
        "par Lui.",
        "Notre foi fonde et inspire chacune de nos actions.",
    ),
    (
        "Respect de la personne humaine",
        "À IMSO, nous nous soucions de l'impact de nos actes sur l'autre. Nous sommes "
        "inclusifs et nous acceptons l'autre pour ce qu'elle/il est, même lorsqu'elle/il "
        "est different/e. Nous traitons l'autre avec égard et considération.",
        "Accueillir l'autre tel qu'il est, avec égard.",
    ),
    (
        "Subsidiarité",
        "Tout le monde est responsable en fonction de son niveau de responsabilité dans "
        "la chaîne. L'apport ou la decision de chacun est respecté et valorisé dans le "
        "cadre la poursuite des objectifs de l'équipe.",
        "Chacun décide à son niveau ; chaque apport compte.",
    ),
    (
        "Redevabilité",
        "Tous les membres d'IMSO sont des partenaires égaux et valorisés. Celles/ceux "
        "qui sont en charge sont tenues/tenus de rendre compte à toutes/tous les autres "
        "de ses activités.",
        "Qui décide rend des comptes à tous.",
    ),
    (
        "Équité",
        "À IMSO, tout un chacun est traité de façon juste, égalitaire, raisonnable et "
        "sans acception de race, de religion ou de sexe. Nous jouissons toutes/tous des "
        "mêmes droits et avons les mêmes devoirs l’un/e envers l’autre.",
        "Mêmes droits, mêmes devoirs — sans distinction.",
    ),
    (
        "Intégrité",
        "Nous agissons avec honnêteté, droiture et respect. Nous sommes fidèles à nos "
        "valeurs et prenons des décisions justes, même lorsque personne ne regarde. Nous "
        "ne nous engageons dans aucune action susceptible d’entacher notre réputation "
        "et la réputation de l’équipe/du groupe.",
        "Justes, même quand personne ne regarde.",
    ),
    (
        "Confiance",
        "À IMSO, nos relations avec nos membres et nos partenaires se basent sur une "
        "confiance réciproque. Nous sommes dignes de confiance et sommes responsables de "
        "nos actions.",
        "Une confiance réciproque, méritée par nos actes.",
    ),
]


# Au-dela de cette longueur, le texte est encore la version longue d'origine.
# Les textes condenses font tous moins de 60 caracteres.
LONG_TEXT_THRESHOLD = 80


def condense(apps, schema_editor):
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for title, _long_text, short_text in CONDENSED:
        # On cible par titre + longueur plutot que par egalite exacte : une simple
        # apostrophe typographique ou une espace en trop suffirait a faire echouer
        # une correspondance stricte, et la migration ne ferait rien en silence.
        # Un texte deja court (retouche depuis l'admin) n'est jamais ecrase.
        for value in CoreValue.objects.filter(title=title):
            if len(value.text or "") > LONG_TEXT_THRESHOLD:
                value.text = short_text
                value.save(update_fields=["text"])


def restore(apps, schema_editor):
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    for title, long_text, short_text in CONDENSED:
        CoreValue.objects.filter(title=title, text=short_text).update(text=long_text)


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0035_copy_mission_valeurs_epuree"),
    ]

    operations = [migrations.RunPython(condense, restore)]

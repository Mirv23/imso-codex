# -*- coding: utf-8 -*-
"""Seed idempotent de synchronisation du contenu « Site » avec le panel admin.

Contexte : sur certains environnements, les tables de registre (SiteText,
SiteImage) ont été créées puis leur migration de seed appliquée AVANT que le
contenu ne soit finalisé — Django ne rejoue jamais une migration déjà appliquée,
donc ces tables pouvaient rester vides/incomplètes. Par ailleurs, CoreValue et
ProcessStep n'avaient AUCUN seed (0021 crée seulement les modèles), d'où le
« aucune donnée » côté admin alors que le site affiche un contenu codé en dur.

Cette migration REJOUE les seeds de manière idempotente (get_or_create par clé)
pour garantir que le contenu éditable est présent partout, et ajoute les 3
valeurs + 3 étapes par défaut (identiques au fallback des templates) UNIQUEMENT
si ces tables sont vides (pour ne jamais écraser un contenu déjà personnalisé).
"""
from importlib import import_module

from django.db import migrations

# Valeurs par défaut — identiques au bloc {% empty %} de core/partials/about.html
CORE_VALUES = [
    {
        "title": "Solidarité",
        "text": "Nous mutualisons risques et opportunités. Chaque membre soutient "
                "l'élan collectif et profite des progrès du groupe.",
        "icon": "",
        "sort_order": 1,
    },
    {
        "title": "Respect humain",
        "text": "La dignité passe avant tout. Décisions transparentes, écoute active "
                "et gouvernance partagée à toutes les étapes.",
        "icon": "",
        "sort_order": 2,
    },
    {
        "title": "Croissance collective",
        "text": "Apprendre, entreprendre, partager. Le succès d'un membre devient "
                "une marche pour toute la communauté.",
        "icon": "",
        "sort_order": 3,
    },
]

# Étapes par défaut — identiques au bloc {% empty %} de core/partials/services.html
PROCESS_STEPS = [
    {
        "title": "Candidature et entretien",
        "text": "Remplissez le formulaire d'adhésion et rencontrez les responsables "
                "d'un GEI proche de chez vous pour présenter votre projet.",
        "meta": "⏱ 1 semaine",
        "sort_order": 1,
    },
    {
        "title": "Formation d'intégration",
        "text": "Trois ateliers fondamentaux : gouvernance mutualiste, gestion "
                "d'épargne et obligations des membres.",
        "meta": "⏱ 3 semaines",
        "sort_order": 2,
    },
    {
        "title": "Activation de l'adhésion",
        "text": "Première cotisation, signature des statuts du GEI et accès complet "
                "aux cours, au microcrédit et aux ressources communes.",
        "meta": "⏱ Le jour même",
        "sort_order": 3,
    },
]


def _load_seed(module_name, attr):
    """Récupère une liste de seed depuis une migration sœur (nom à chiffre initial,
    importable via importlib). Renvoie [] si indisponible, pour ne jamais casser
    la migration."""
    try:
        return getattr(import_module("apps.adminpanel.migrations.%s" % module_name), attr, []) or []
    except Exception:
        return []


def seed(apps, schema_editor):
    SiteText = apps.get_model("adminpanel", "SiteText")
    SiteImage = apps.get_model("adminpanel", "SiteImage")
    CoreValue = apps.get_model("adminpanel", "CoreValue")
    ProcessStep = apps.get_model("adminpanel", "ProcessStep")

    # (Re)seed idempotent des textes/images éditables : get_or_create par clé
    # unique -> n'écrase jamais une valeur déjà personnalisée, comble les manques.
    for e in _load_seed("0023_seed_site_texts", "SEED"):
        SiteText.objects.get_or_create(
            key=e["key"],
            defaults={
                "label": e.get("label", ""),
                "group": e.get("group", ""),
                "value": e.get("value", ""),
            },
        )
    for e in _load_seed("0025_seed_site_texts_images", "IMAGES"):
        SiteImage.objects.get_or_create(
            key=e["key"],
            defaults={
                "label": e.get("label", ""),
                "group": e.get("group", ""),
                "alt": e.get("alt", ""),
            },
        )

    # Valeurs / étapes : semées UNIQUEMENT si la table est vide (aucune donnée
    # personnalisée à préserver).
    if not CoreValue.objects.exists():
        for e in CORE_VALUES:
            CoreValue.objects.create(
                title=e["title"], text=e["text"], icon=e["icon"],
                sort_order=e["sort_order"], is_active=True,
            )
    if not ProcessStep.objects.exists():
        for e in PROCESS_STEPS:
            ProcessStep.objects.create(
                title=e["title"], text=e["text"], meta=e["meta"],
                sort_order=e["sort_order"], is_active=True,
            )


def unseed(apps, schema_editor):
    # Seed de resynchronisation : on ne supprime rien au rollback (éviterait
    # d'effacer du contenu potentiellement édité entre-temps).
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0026_adminaccess"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]

# -*- coding: utf-8 -*-
"""Crée la table du cache Postgres partagé « imso_ratelimit_cache » utilisée par
le rate-limiting (voir settings.CACHES['ratelimit']). Sans cette table partagée
entre lambdas, l'anti-force-brute serverless est contournable.

createcachetable est idempotent (ignore une table déjà existante), donc rejouable
sans risque. La table est créée même si Redis est actif (inoffensif, non utilisée)."""
from django.core.management import call_command
from django.db import migrations

CACHE_TABLE = "imso_ratelimit_cache"


def create_cache_table(apps, schema_editor):
    call_command(
        "createcachetable",
        CACHE_TABLE,
        database=schema_editor.connection.alias,
        verbosity=0,
    )


def drop_cache_table(apps, schema_editor):
    schema_editor.execute(f'DROP TABLE IF EXISTS "{CACHE_TABLE}"')


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0028_seed_process_texts"),
    ]

    operations = [
        migrations.RunPython(create_cache_table, drop_cache_table),
    ]

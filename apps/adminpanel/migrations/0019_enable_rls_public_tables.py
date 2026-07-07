"""Active Row Level Security (RLS) sur toutes les tables du schéma public.

Contexte : la base est hébergée sur Supabase, dont le « Data API » (PostgREST)
expose le schéma `public`. Sans RLS, les rôles `anon`/`authenticated` peuvent
lire n'importe quelle table via l'API REST auto-générée — y compris des colonnes
sensibles (auth_user.password, Admin.password, paymentprovider.account_number).
Le linter Supabase remonte cela en ERROR (rls_disabled_in_public,
sensitive_columns_exposed).

Correctif : activer RLS sans policy permissive => refus total pour les rôles non
privilégiés (anon/authenticated). L'application Django n'est PAS affectée : elle
se connecte en `postgres`, propriétaire des tables ET porteur de l'attribut
BYPASSRLS — il contourne donc RLS des deux façons.

Idempotent (ENABLE sur une table déjà protégée est sans effet). Ne s'exécute que
sur PostgreSQL : sur SQLite (tests/dev) c'est un no-op pour éviter une erreur de
syntaxe.
"""

from django.db import migrations


ENABLE_SQL = """
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', r.tablename);
  END LOOP;
END $$;
"""

DISABLE_SQL = """
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY;', r.tablename);
  END LOOP;
END $$;
"""


def _run(sql):
    def _inner(apps, schema_editor):
        # RLS n'existe que sous PostgreSQL ; no-op ailleurs (SQLite en tests).
        if schema_editor.connection.vendor != "postgresql":
            return
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)
    return _inner


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0018_sitesetting_tiktok_url"),
    ]

    operations = [
        migrations.RunPython(_run(ENABLE_SQL), _run(DISABLE_SQL)),
    ]

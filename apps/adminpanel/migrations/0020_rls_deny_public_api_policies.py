"""Ajoute une policy « deny-all » explicite sur chaque table du schéma public.

Suite à la migration 0019 (RLS activée sans policy), le linter Supabase remonte
41 avis INFO `rls_enabled_no_policy` (« RLS active mais aucune policy »). Ce n'est
pas une faille — sans policy, l'accès des rôles PostgREST (anon/authenticated) est
déjà refusé par défaut. On ajoute néanmoins une policy restrictive explicite
`USING (false)` afin de :
  - rendre l'intention explicite (refus total via l'API auto-générée),
  - faire disparaître les avis INFO du linter.

Aucun impact sur Django : il se connecte en `postgres` (propriétaire des tables +
BYPASSRLS) et n'est donc jamais soumis aux policies. Idempotent (DROP IF EXISTS
puis CREATE). No-op hors PostgreSQL (tests SQLite).
"""

from django.db import migrations


CREATE_SQL = """
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', 'deny_public_api', r.tablename);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);',
      'deny_public_api', r.tablename
    );
  END LOOP;
END $$;
"""

DROP_SQL = """
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', 'deny_public_api', r.tablename);
  END LOOP;
END $$;
"""


def _run(sql):
    def _inner(apps, schema_editor):
        if schema_editor.connection.vendor != "postgresql":
            return
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)
    return _inner


class Migration(migrations.Migration):

    dependencies = [
        ("adminpanel", "0019_enable_rls_public_tables"),
    ]

    operations = [
        migrations.RunPython(_run(CREATE_SQL), _run(DROP_SQL)),
    ]

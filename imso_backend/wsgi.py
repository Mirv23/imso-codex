import os
import sys

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imso_backend.settings")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def _setup():
    django.setup()
    _run_startup_migrations()


def _run_startup_migrations():
    if os.environ.get("RUN_MIGRATIONS_ON_STARTUP", "").lower() in ("1", "true", "yes"):
        from django.core.management import call_command

        try:
            call_command("migrate", "--noinput")
        except Exception as e:
            print(f"[startup] Migration failed: {e}", flush=True)

        try:
            call_command("ensure_admin")
        except Exception as e:
            print(f"[startup] ensure_admin failed: {e}", flush=True)


_setup()

app = get_wsgi_application()
application = app

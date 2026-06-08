import os

import django
from django.core.wsgi import get_wsgi_application
from django.db import connection


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imso_backend.settings")


def _setup():
    django.setup()
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1 FROM django_migrations LIMIT 1")
    except Exception:
        from django.core.management import call_command
        call_command("migrate", "--noinput")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        username = os.environ.get("ADMIN_USERNAME", "mirv")
        password = os.environ.get("ADMIN_PASSWORD", "")
        email = os.environ.get("ADMIN_EMAIL", "admin@imsohaiti.com")
        if password:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "is_staff": True, "is_superuser": True},
            )
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()


_setup()

app = get_wsgi_application()
application = app

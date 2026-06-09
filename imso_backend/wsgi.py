import os

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imso_backend.settings")


def _setup():
    django.setup()


_setup()

app = get_wsgi_application()
application = app

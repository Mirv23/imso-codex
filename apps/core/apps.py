import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_admin(sender, **kwargs):
    from django.contrib.auth import get_user_model

    username = os.environ.get("ADMIN_USERNAME", "mirv")
    password = os.environ.get("ADMIN_PASSWORD", "")
    email = os.environ.get("ADMIN_EMAIL", "admin@imsohaiti.com")
    if not password:
        return
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email, "is_staff": True, "is_superuser": True},
    )
    user.set_password(password)
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.save()


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        post_migrate.connect(create_admin, sender=self)

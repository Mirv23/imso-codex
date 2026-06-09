#!/usr/bin/env python
"""
Script de migration pour Vercel Post-Deploy Hook.
Usage: python scripts/vercel-migrate.py

À appeler après chaque déploiement via:
  - Vercel Post-Deploy Hook (vercel.json)
  - Ou manuellement via SSH
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "imso_backend.settings")

import django
from django.core.management import call_command
from django.db import connection

django.setup()

# Vérifier la connexion DB
try:
    connection.ensure_connection()
    print("✓ DB connected")
except Exception as e:
    print(f"✗ DB connection failed: {e}")
    sys.exit(1)

# Appliquer les migrations
try:
    call_command("migrate", "--noinput")
    print("✓ Migrations applied")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)

# Créer le superuser si nécessaire
username = os.environ.get("ADMIN_USERNAME")
password = os.environ.get("ADMIN_PASSWORD")
if username and password:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = os.environ.get("ADMIN_EMAIL", "admin@imsohaiti.com")
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email, "is_staff": True, "is_superuser": True},
    )
    user.set_password(password)
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✓ Admin user '{username}' {'created' if created else 'updated'}")

print("✓ Setup complete")

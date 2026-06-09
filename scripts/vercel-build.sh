#!/bin/bash
echo "==> IMSO Build Script"
echo "==> Collecting static files..."
python manage.py collectstatic --noinput
echo "==> Build complete"

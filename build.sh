#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

if [ "${SIMTECH_RUN_SEED:-}" = "true" ]; then
  python manage.py seed_school
fi

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py createsuperuser --noinput || true
fi

#!/usr/bin/env bash
set -o errexit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

: "${DJANGO_SUPERUSER_USERNAME:?DJANGO_SUPERUSER_USERNAME is not set}"
: "${DJANGO_SUPERUSER_EMAIL:?DJANGO_SUPERUSER_EMAIL is not set}"
: "${DJANGO_SUPERUSER_PASSWORD:?DJANGO_SUPERUSER_PASSWORD is not set}"

python manage.py migrate --noinput

python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ['DJANGO_SUPERUSER_USERNAME']
email = os.environ['DJANGO_SUPERUSER_EMAIL']
password = os.environ['DJANGO_SUPERUSER_PASSWORD']

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email}
)
user.email = email
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()
print(f'Created superuser: {username}' if created else f'Updated superuser: {username}')
"
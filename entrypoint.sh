#!/bin/sh

set -e

echo "Waiting for database..."
# Replace `db` with your docker-compose service name for the database
while ! nc -z db 5432; do
  sleep 1
done

echo "Database ready!"

# Apply migrations and collect static files
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "Checking for superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email="${DJANGO_SUPERUSER_EMAIL}",
        password="${DJANGO_SUPERUSER_PASSWORD}"
    )
    print(f"Superuser '{username}' created.")
else:
    print(f"Superuser '{username}' already exists.")
EOF

# Start Gunicorn
exec gunicorn app.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120

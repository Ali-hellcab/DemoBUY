release: python manage.py migrate --noinput
web: gunicorn demobuy.wsgi:application --bind 0.0.0.0:$PORT

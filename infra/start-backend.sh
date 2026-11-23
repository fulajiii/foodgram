#!/bin/sh
set -eu

python -u manage.py migrate --noinput
python -u manage.py collectstatic --noinput
python -u manage.py load_ingredients
exec gunicorn --bind 0.0.0.0:8000 foodgram.wsgi

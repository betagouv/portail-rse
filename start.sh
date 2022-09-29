#! /bin/bash

python impact/manage.py collectstatic --no-input
python impact/manage.py migrate
gunicorn --pythonpath=impact impact.wsgi --log-file -

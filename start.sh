#! /bin/bash

python impact/manage.py collectstatic --no-input

gunicorn --pythonpath=impact impact.wsgi --log-file -

#! /bin/bash

python impact/manage.py collectstatic --no-input
python impact/manage.py migrate
python impact/manage.py migrate metabase --database=metabase

gunicorn --pythonpath=impact impact.wsgi --log-file -

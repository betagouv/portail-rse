#! /bin/bash
set -e

echo "-----> Running collectstatic"
python impact/manage.py collectstatic --no-input

echo "-----> Starting gunicorn on unix socket"
# Démarrer gunicorn sur un socket Unix (nginx fait proxy depuis $PORT)
gunicorn impact.wsgi --pythonpath=impact --bind unix:/tmp/gunicorn.sock --log-file -

#! /bin/bash

source ./venv/bin/activate
set -a
source .env
set +a
./venv/bin/python3 impact/manage.py runserver
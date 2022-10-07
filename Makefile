include .env
export

run:
	./venv/bin/python3 impact/manage.py runserver

install:
	python3 -m venv venv
	./venv/bin/pip install pipenv
	./venv/bin/pipenv install

shell:
	./venv/bin/python3 impact/manage.py shell

migrate:
	./venv/bin/python3 impact/manage.py migrate

migrations:
	./venv/bin/python3 impact/manage.py makemigrations public users

createsuperuser:
	./venv/bin/python3 impact/manage.py createsuperuser

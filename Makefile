include .env
export

run:
	pipenv run python impact/manage.py runserver

install:
	pipenv install -d
	pipenv run pre-commit install

shell:
	pipenv run python impact/manage.py shell

migrate:
	pipenv run python impact/manage.py migrate

migrations:
	pipenv run python impact/manage.py makemigrations entreprises public reglementations users

createsuperuser:
	pipenv run python impact/manage.py createsuperuser

test:
	pipenv run pytest

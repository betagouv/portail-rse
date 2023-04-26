include .env
export

run:
	honcho --procfile Procfile.dev start

install:
	pipenv install -d
	npm install
	pipenv run pre-commit install

shell:
	pipenv run python impact/manage.py shell

migrate:
	pipenv run python impact/manage.py migrate
	pipenv run python impact/manage.py migrate metabase --database=metabase

migrations:
	pipenv run python impact/manage.py makemigrations entreprises habilitations metabase public reglementations users

sync_metabase:
	pipenv run impact/manage.py sync_metabase

createsuperuser:
	pipenv run python impact/manage.py createsuperuser

test:
	pipenv run pytest

test-fast:
	pipenv run pytest --no-migrations -m "not slow"

include .env
export

run:
	honcho --procfile Procfile.dev start

web:
# utile pour débugger en ajoutant des breakpoint() dans le code et permettre leur exécution dans le terminal sans interception des commandes par honcho
	PYTHONUNBUFFERED=true python impact/manage.py runserver

install:
	pipenv install -d
	npm ci --ignore-scripts
	pipenv run pre-commit install

shell:
	pipenv run python impact/manage.py shell

migrate:
	pipenv run python impact/manage.py migrate
	pipenv run python impact/manage.py migrate metabase --database=metabase

migrations:
	pipenv run python impact/manage.py makemigrations entreprises habilitations invitations metabase public reglementations users vsme

sync_metabase:
	pipenv run impact/manage.py sync_metabase

createsuperuser:
	pipenv run python impact/manage.py createsuperuser

test:
	pipenv run pytest

test-fast:
	pipenv run pytest --no-migrations -m "not slow"

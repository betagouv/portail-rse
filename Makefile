include .env
export

run:
	uv run honcho --procfile Procfile.dev start

web:
# utile pour débugger en ajoutant des breakpoint() dans le code et permettre leur exécution dans le terminal sans interception des commandes par honcho
	PYTHONUNBUFFERED=true python impact/manage.py runserver

install:
	uv sync --group dev
	npm ci --ignore-scripts
	uv run pre-commit install

shell:
	uv run python impact/manage.py shell

migrate:
	uv run python impact/manage.py migrate
	uv run python impact/manage.py migrate metabase --database=metabase

migrations:
	uv run python impact/manage.py makemigrations entreprises habilitations invitations metabase public reglementations users vsme

sync_metabase:
	uv run impact/manage.py sync_metabase

createsuperuser:
	uv run python impact/manage.py createsuperuser

test:
	uv run pytest

test-fast:
	uv run pytest --no-migrations -m "not slow"

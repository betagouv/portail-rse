run:
	. ./venv/bin/activate; \
	set -a; \
	. .env; \
	set +a; \
	./venv/bin/python3 impact/manage.py runserver

install:
	python3 -m venv venv
	./venv/bin/pip install pipenv
	pipenv install

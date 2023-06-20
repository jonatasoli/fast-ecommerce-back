.PHONY: install update shell format lint test sec export configs upgrade run migrate


install:
	@poetry install

update:
	@poetry update

shell:
	@poetry shell

format:
	@blue . 

lint:
	@blue . --check
	@ruff check .

test:
	@pytest -s tests

configs:
	dynaconf -i src.config.settings list

upgrade:
	@poetry run alembic upgrade head

run:
	@poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8001

migrate:
	@poetry run alembic revision --autogenerate

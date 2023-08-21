.PHONY: install update shell format lint test sec export configs upgrade run migrate post-test worker


install:
	@poetry install

update:
	@poetry update

shell:
	@poetry shell

format:
	@blue app/ 
	@blue tests/ 

lint:
	@blue app/ tests/ --check
	@ruff check app/
	@ruff check tests/entities --ignore S101

test:
	FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/entities -x --cov=fast_ecommerce -vv
	FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/endpoints/cart -x --cov=fast_ecommerce -vv
	FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/services -x --cov=fast_ecommerce -vv
	FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/models -x --cov=fast_ecommerce -vv

post-test:
	@coverage html

configs:
	dynaconf -i src.config.settings list

upgrade:
	@poetry run alembic upgrade head

run:
	@poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8001

migrate:
	@poetry run alembic revision --autogenerate

worker:
	@celery -A app.worker:celery worker --loglevel=info

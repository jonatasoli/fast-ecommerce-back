.PHONY: install update shell format lint test sec export configs upgrade run migrate post-test


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
	@ruff check app/entities
	@ruff check app/cart/services.py
	@ruff check app/catalog/services.py
	@ruff check app/payment/services.py
	@ruff check app/report/services.py
	@ruff check app/user/services.py
	@ruff check app/infra/endpoints
	# @ruff check tests/ --ignore S101

test:
	FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/ ex --cov=fast_ecommerce -vv

post_test:
	@coverage html

configs:
	dynaconf -i src.config.settings list

upgrade:
	@poetry run alembic upgrade head

run:
	@poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8001

migrate:
	@poetry run alembic revision --autogenerate

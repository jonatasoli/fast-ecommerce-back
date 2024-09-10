.PHONY: install update shell format lint test sec export configs upgrade run migrate post-test task


install:
	@uv install

update:
	@uv update

shell:
	@uv shell

format:
	# @blue app/ 
	# @blue tests/ 
	@ruff check . --fix

lint:
	# @blue app/ tests/ --check
	@ruff check app/entities
	@ruff check app/cart/services.py
	@ruff check app/catalog/services.py
	@ruff check app/payment/services.py
	@ruff check app/report/services.py
	@ruff check app/user/services.py
	@ruff check app/infra/endpoints
	# @ruff check tests/ --ignore S101

test:
	@uv run FORCE_ENV_FOR_DYNACONF=testing pytest -s tests/ -x --cov=fast_ecommerce -vv

post_test:
	@coverage html

configs:
	dynaconf -i src.config.settings list

upgrade:
	@uv run alembic upgrade head

run:
	@uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

migrate:
	@uv run alembic revision --autogenerate

task:
	@uv run taskiq scheduler app.infra.scheduler:scheduler

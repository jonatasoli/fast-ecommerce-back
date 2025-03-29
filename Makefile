.PHONY: install update shell format lint test sec export configs upgrade run migrate post-test task


install:
	@uv install

update:
	@uv update

shell:
	@uv shell

format:
	@ruff check . --fix

lint:
	@ruff check app/entities
	@ruff check app/cart/services.py
	@ruff check app/catalog
	@ruff check app/coupons
	@ruff check app/payment/tasks.py
	@ruff check app/payment/services.py
	@ruff check app/payment/repository.py
	@ruff check app/freight
	@ruff check app/report
	@ruff check app/user/tasks.py
	@ruff check app/user/services.py
	@ruff check app/user/repository.py
	@ruff check app/inventory/tasks.py
	@ruff check app/inventory/repository.py
	@ruff check app/mail
	@ruff check app/order/tasks.py
	@ruff check app/order/services.py
	@ruff check app/order/repository.py
	@ruff check app/product
	@ruff check app/settings
	@ruff check app/infra/endpoints
	@ruff check tests/ --ignore S101

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

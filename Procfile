web: poetry run opentelemetry-instrument --logs_exporter console,otlp uvicorn main:app --workers 2 --host 0.0.0.0 --port $PORT
tasks: poetry run taskiq scheduler app.infra.scheduler:scheduler
migration: poetry run alembic upgrade head

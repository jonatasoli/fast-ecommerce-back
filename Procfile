web: uv run uvicorn main:app --port $PORT --host 0.0.0.0
tasks: uv run taskiq scheduler app.infra.scheduler:scheduler
migration: uv run alembic upgrade head

web: uv run uvicorn main:app --port $PORT --host 0.0.0.0
task: uv run taskiq scheduler app.infra.scheduler:scheduler
order_task: uv run taskiq scheduler app.infra.scheduler_order:scheduler

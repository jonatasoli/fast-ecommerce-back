web: poetry run opentelemetry-instrument --logs_exporter console,otlp uvicorn main:app --workers 2 --host 0.0.0.0 --port $PORT
worker: 2
tasks: make task

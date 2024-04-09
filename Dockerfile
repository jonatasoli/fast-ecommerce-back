FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTCODE=1 \
	PIP_NO_CACHE_DIR=off \
	PIP_DEFAULT_TIMEOUT=100 \
	POETRY_HOME="/opt/poetry" \
	POETRY_VIRTUALENVS_CREATE=0 \
  PYTHONPATH=/app

ENV PATH="$PATH:$POETRY_HOME/bin"

RUN apt-get update -y && apt install build-essential curl --no-install-recommends -y 

WORKDIR /app/

COPY . /app

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry config virtualenvs.create false
RUN poetry install --without dev
RUN poetry run opentelemetry-bootstrap --action=install

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTCODE=1 \
	PIP_NO_CACHE_DIR=off \
	PIP_DEFAULT_TIMEOUT=100 \
	POETRY_HOME="/opt/poetry" \
	POETRY_VIRTUALENVS_CREATE=false \
  PYTHONPATH=/app

ENV PATH="$PATH:$POETRY_HOME/bin"

WORKDIR /app/

RUN apt-get update -y && apt install build-essential curl --no-install-recommends -y && curl -sSL https://install.python-poetry.org | python3 -

COPY . /app

poetry install --without dev

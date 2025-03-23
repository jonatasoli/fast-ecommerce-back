FROM python:3.13-bookworm

RUN apt-get update && apt install build-essential libpq5 curl \
    -y --no-install-recommends

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app/
COPY . /app

RUN uv sync --frozen --no-cache

FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl && \
    libpq5 \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

FROM python:3.13-slim-bookworm

COPY --from=builder /bin/uv /bin/uv
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    UV_NO_WARN_SCRIPT_LOCATION=0 \
    PATH="/home/appuser/.local/bin:${PATH}"

RUN useradd --create-home appuser && \
    mkdir -p /app && \
    chown appuser:appuser /app

WORKDIR /app
USER appuser

COPY --chown=appuser:appuser . .

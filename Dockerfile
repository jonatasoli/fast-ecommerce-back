FROM python:3.12-slim

ENV POETRY_VIRTUALENVS_CREATE=false


RUN apt-get update -y && apt install build-essential curl --no-install-recommends -y 

WORKDIR /app/

COPY . /app

RUN pip install poetry
RUN poetry install --without dev
RUN opentelemetry-bootstrap -a install

FROM python:3.7-slim

WORKDIR /app/

RUN apt install python3-bs4

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY ./app /app
ENV PYTHONPATH=/app

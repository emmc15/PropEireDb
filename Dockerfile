FROM python:3.11-slim-bookworm

WORKDIR /workspace
ENV PYTHONPATH=${PYTHONPATH}:${PWD} 

COPY ./pyproject.toml  pyproject.toml
COPY ./poetry.lock poetry.lock
RUN apt update && apt install build-essential gcc git wget -y && pip3 install poetry && poetry config virtualenvs.create false && poetry install

COPY ./ /workspace/

# CMD cd src && gunicorn wsgi:server -c gunicorn.conf.py
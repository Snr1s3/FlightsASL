FROM python:3.11-slim

WORKDIR /app

RUN pip install --upgrade pip && pip install poetry
ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

COPY src/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
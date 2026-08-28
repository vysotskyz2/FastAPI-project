# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS builder
ENV POETRY_VERSION=2.4.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root

FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -m app
COPY --from=builder /app/.venv /app/.venv
COPY --chown=app:app src ./src
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
USER app
EXPOSE 8000
CMD ["uvicorn", "src.interfaces.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

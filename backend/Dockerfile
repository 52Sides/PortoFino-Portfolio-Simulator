FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    redis-tools \
    netcat-openbsd \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY entrypoint.sh ./entrypoint.sh
COPY src ./src

RUN pip install --upgrade pip && pip install -e .

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
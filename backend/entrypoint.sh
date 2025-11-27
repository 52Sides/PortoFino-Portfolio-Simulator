#!/bin/sh
set -e


echo "Waiting for Postgres..."
until pg_isready -h postgres -p 5432 -U postgres; do sleep 2; done

echo "Waiting for Redis..."
until [ "$(redis-cli -h redis ping)" = "PONG" ]; do sleep 2; done

echo "Waiting for Kafka..."
until nc -z kafka 9092; do sleep 3; done


ALEMBIC_FILE="/app/src/db/migrations/alembic.ini"
if [ -f "$ALEMBIC_FILE" ]; then
  echo "Running Alembic migrations..."
  alembic -c "$ALEMBIC_FILE" upgrade head
else
  echo "Warning: Alembic config not found at $ALEMBIC_FILE, skipping migrations"
fi


cd /app/src || { echo "Directory /app/src not found"; exit 1; }
exec uvicorn api.main:app --host 0.0.0.0 --port 8000

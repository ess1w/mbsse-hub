#!/bin/sh
# Production startup script — runs on every Render deploy.
# Safe to re-run: migrations and seed scripts are idempotent.
set -e

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Seeding admin user..."
python seed_admin.py

echo "==> Seeding partner organisations..."
python seed_organisations.py

echo "==> Starting API server on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 2

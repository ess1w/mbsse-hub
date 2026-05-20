#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding admin user..."
python seed_admin.py

echo "Seeding partner organisations..."
python seed_organisations.py

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

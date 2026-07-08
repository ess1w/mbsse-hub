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

echo "==> Seeding chiefdoms reference data..."
python seed_chiefdoms.py

echo "==> Seeding additional partner organisations (SEND SL, FOCUS 1000)..."
python seed_new_partners.py

echo "==> Seeding additional partner login accounts..."
python seed_new_partner_users.py

echo "==> Seeding demo users (partner + viewer)..."
python seed_users.py

echo "==> Seeding demo submissions..."
python seed_submissions.py

echo "==> Seeding pilot partner users..."
python seed_pilot_users.py

echo "==> Seeding sample data for analytics (Jan-Feb + Mar-Apr 2026)..."
python seed_sample_data.py

echo "==> Cleaning up demo submissions (production only)..."
python cleanup_demo_submissions.py

echo "==> Starting API server on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 2

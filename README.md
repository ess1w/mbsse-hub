# MBSSE School Safety Coordination Hub

Sierra Leone MBSSE SRGBV partner coordination platform.

---

## Quick start — Docker (recommended)

```bash
cd /Users/danielchaytor/Documents/Clients/MBSSE
docker compose up --build
```

This starts:
| Service | URL |
|---------|-----|
| Frontend (Vite/React) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

On first boot the backend automatically:
1. Runs Alembic migrations
2. Seeds admin user (`admin@mbsse.gov.sl` / `changeme123`)
3. Seeds 22 partner organisations + projects

---

## Quick start — Local dev

### Prerequisites
- Python 3.11+ (a venv is at `backend/venv/`)
- Node 18+
- PostgreSQL running locally

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Set env vars (or edit .env)
export DATABASE_URL="postgresql+asyncpg://USER@localhost:5432/mbsse_hub"
export SECRET_KEY="dev-secret"

# Migrate
alembic upgrade head

# Seed
python seed_admin.py
python seed_organisations.py

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd prototype
npm install
# Create .env.local
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

---

## Database schema

Follows data dictionary Sections 5.1–5.7 from the Inception Report v5.

| Table | Purpose |
|-------|---------|
| `organisations` | Partner org registry (§5.1) |
| `projects` | Project registry (§5.2) |
| `districts` / `chiefdoms` | Geographic reference (§5.3) |
| `submissions` | Bi-monthly reports |
| `activities` | Per-activity classification (§5.5) |
| `submission_locations` | Geographic coverage per submission (§5.6) |
| `output_indicators` | Numeric output data per activity (§5.7) |
| `users` / `token_blacklist` | Auth |
| `reporting_periods` | Active cycle management |

---

## Default credentials

| Email | Password | Role |
|-------|----------|------|
| admin@mbsse.gov.sl | changeme123 | Admin |

**Change the admin password after first login.**

---

## Architecture

```
mbsse/
├── docker-compose.yml        # Three services: postgres, backend, frontend
├── backend/                  # FastAPI + SQLAlchemy 2.0 + asyncpg
│   ├── app/
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── api/routes/       # FastAPI routers
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   └── core/             # Config, security, deps
│   ├── alembic/              # DB migrations
│   ├── seed_admin.py
│   └── seed_organisations.py
└── prototype/                # React 18 + Vite 4
    └── src/
        ├── components/
        │   ├── Dashboard.jsx
        │   ├── directory/PartnerDirectory.jsx
        │   └── form/ReportingForm.jsx
        ├── api/client.js     # API client with JWT refresh
        └── data/             # Static reference data
```

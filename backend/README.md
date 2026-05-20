# MBSSE Hub — FastAPI Backend

## Quick start (local)

```bash
cd backend

# 1. Python env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Copy and fill in env vars
cp .env.example .env

# 3. PostgreSQL — create the database
createdb mbsse_hub
psql mbsse_hub < schema.sql        # create tables + seed districts

# 4. Run migrations (after schema changes use Alembic instead)
alembic upgrade head

# 5. Start API
uvicorn app.main:app --reload --port 8000

# 6. Start Celery worker (separate terminal)
celery -A app.tasks.celery_app.celery worker --loglevel=info

# 7. Start Celery beat scheduler (separate terminal)
celery -A app.tasks.celery_app.celery beat --loglevel=info
```

API docs at http://localhost:8000/docs

---

## Auth flow

| Step | Endpoint | Notes |
|---|---|---|
| Login | `POST /api/v1/auth/login` | Returns access + refresh tokens |
| Use API | `Authorization: Bearer <access_token>` | 60-min expiry |
| Refresh | `POST /api/v1/auth/refresh` | Returns new access token |
| Logout | `POST /api/v1/auth/logout` | Blacklists token JTI |

---

## Role permission matrix

| Action | admin | viewer | partner |
|---|---|---|---|
| List all submissions | ✅ | ✅ | Own org only |
| Create / save draft | ✅ | ❌ | Own org only |
| Submit report | ✅ | ❌ | Own org only |
| Patch status / flag | ✅ | ❌ | ❌ |
| Upload files | ✅ | ❌ | Own org only |
| Manage users | ✅ | ❌ | ❌ |
| View audit log | ✅ | ❌ | ❌ |

---

## Automated reminders schedule

Celery beat runs daily at 08:00 WAT. Reminder emails are sent at:
- **14 days before deadline** — first heads-up
- **7 days before deadline** — second reminder
- **1 day before deadline** — final warning
- **Day after deadline** — overdue notice

Each reminder is idempotent (logged in `reminders` table; won't re-send same type twice).

---

## File uploads

- `POST /api/v1/submissions/{id}/files?file_kind=photo`  
- `POST /api/v1/submissions/{id}/files?file_kind=document`

Local dev: stored in `./uploads/` and served at `/uploads/`  
Production: set `STORAGE_BACKEND=s3` and configure AWS credentials.

---

## Deployment on Render

| Service | Type | Config |
|---|---|---|
| API | Web Service | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Worker | Background Worker | `celery -A app.tasks.celery_app.celery worker` |
| Beat | Background Worker | `celery -A app.tasks.celery_app.celery beat` |
| DB | PostgreSQL | Render managed Postgres |
| Cache | Redis | Render managed Redis |

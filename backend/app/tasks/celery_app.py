from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "mbsse",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.reminders"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Africa/Freetown",
    enable_utc=True,
)

# ── Scheduled jobs ────────────────────────────────────────────────────────────
celery.conf.beat_schedule = {
    # Every morning at 08:00 WAT — check deadlines and queue reminders
    "check-submission-deadlines": {
        "task": "app.tasks.reminders.check_and_queue_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    # Every night at 02:00 — purge expired blacklisted tokens
    "purge-expired-tokens": {
        "task": "app.tasks.reminders.purge_expired_tokens",
        "schedule": crontab(hour=2, minute=0),
    },
}

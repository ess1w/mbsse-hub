"""
APScheduler jobs for the MBSSE Hub.

Jobs are registered at app startup via lifespan() in main.py.

Scheduled jobs
--------------
send_cycle_reminders
    Runs on the 1st of each bi-monthly reporting cycle start month
    (January, March, May, July, September, November) at 08:00 UTC.
    Finds every partner org that has NO submission (or only a draft) for
    the active reporting period and emails the focal person.

purge_expired_tokens
    Runs daily at 03:00 UTC to clean up the JWT blacklist table.
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


# ── Reminder job ──────────────────────────────────────────────────────────────

async def send_cycle_reminders() -> int:
    """
    Core reminder logic — also called directly by the manual bulk-send endpoint.

    Returns the number of reminders successfully queued / sent.
    """
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.reporting_period import ReportingPeriod
    from app.models.organisation import Organisation
    from app.models.user import User
    from app.models.submission import Submission
    from app.models.reminder import Reminder
    from app.services.email import send_email
    from app.core.config import get_settings

    settings = get_settings()
    sent_count = 0

    async with AsyncSessionLocal() as db:
        # Find the active reporting period
        period = await db.scalar(
            select(ReportingPeriod).where(ReportingPeriod.is_active == True)
        )
        if not period:
            logger.warning("send_cycle_reminders: no active reporting period found")
            return 0

        # Orgs that already have a submitted (or verified) report — skip them
        submitted_org_ids: set = set(
            (await db.scalars(
                select(Submission.org_id).where(
                    Submission.reporting_period_id == period.id,
                    Submission.status.in_(["submitted", "verified"]),
                )
            )).all()
        )

        # All active organisations
        orgs = (await db.scalars(
            select(Organisation).where(Organisation.status == "Active")
        )).all()

        for org in orgs:
            if org.org_id in submitted_org_ids:
                continue   # already submitted — skip

            contact_email = org.email
            contact_name = org.focal_person or "Partner"

            if not contact_email:
                logger.debug("Skipping %s — no contact email", org.org_name)
                continue

            # Idempotency: skip if a reminder was already sent for this org×period
            already_sent = await db.scalar(
                select(Reminder).where(
                    Reminder.organisation_id == org.org_id,
                    Reminder.reporting_period_id == period.id,
                    Reminder.reminder_type == "cycle_start",
                    Reminder.status == "sent",
                )
            )
            if already_sent:
                logger.debug(
                    "Skipping %s — cycle_start reminder already sent for period %s",
                    org.org_name, period.label,
                )
                continue

            # Build and send email
            subject, html = _build_email(
                org_name=org.org_name,
                focal_name=contact_name,
                period_label=period.label,
                deadline=period.deadline.isoformat(),
                frontend_url=settings.frontend_url,
            )

            reminder = Reminder(
                reporting_period_id=period.id,
                organisation_id=org.org_id,
                sent_to_email=contact_email,
                reminder_type="cycle_start",
                status="pending",
                scheduled_for=datetime.now(timezone.utc),
            )
            db.add(reminder)
            await db.flush()   # get reminder.id

            try:
                await send_email(to=contact_email, subject=subject, html_body=html)
                reminder.status = "sent"
                reminder.sent_at = datetime.now(timezone.utc)
                sent_count += 1
                logger.info("Reminder sent → %s <%s>", org.org_name, contact_email)
            except Exception as exc:
                reminder.status = "failed"
                reminder.error_message = str(exc)
                logger.error(
                    "Failed to send reminder to %s: %s", contact_email, exc
                )

        await db.commit()

    return sent_count


def _build_email(
    org_name: str,
    focal_name: str,
    period_label: str,
    deadline: str,
    frontend_url: str,
) -> tuple[str, str]:
    hub_url = f"{frontend_url}/form"
    subject = f"[MBSSE Hub] Activity report due — {period_label}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;color:#1a1a2e">
      <div style="background:#1F5C99;padding:16px 24px;border-radius:8px 8px 0 0">
        <span style="color:#fff;font-size:16px;font-weight:600">
          MBSSE School Safety Coordination Hub
        </span>
      </div>
      <div style="background:#fff;padding:24px;border:1px solid #e2e8f0;
                  border-top:none;border-radius:0 0 8px 8px">
        <p>Dear {focal_name},</p>
        <p>A new reporting cycle has opened for the <strong>{period_label}</strong> period.</p>
        <p>Please log in and submit <strong>{org_name}</strong>'s activity report
           by <strong>{deadline}</strong>.</p>
        <p style="margin:24px 0">
          <a href="{hub_url}"
             style="background:#1F5C99;color:#fff;padding:10px 20px;border-radius:6px;
                    text-decoration:none;font-weight:500">
            Submit your report →
          </a>
        </p>
        <p>If you have already submitted or have questions, please contact
           <a href="mailto:hub@mbsse.gov.sl">hub@mbsse.gov.sl</a>.</p>
        <hr style="border:none;border-top:1px solid #f1f5f9;margin:20px 0"/>
        <p style="font-size:11px;color:#94a3b8">
          Ministry of Basic and Senior Secondary Education, Sierra Leone<br/>
          School Safety Coordination Hub
        </p>
      </div>
    </div>
    """
    return subject, html


# ── Token cleanup job ─────────────────────────────────────────────────────────

async def purge_expired_tokens() -> None:
    from sqlalchemy import delete
    from app.db.session import AsyncSessionLocal
    from app.models.token_blacklist import TokenBlacklist

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        await db.commit()
        logger.info("Purged %d expired JWT blacklist entries", result.rowcount)


# ── Scheduler setup ───────────────────────────────────────────────────────────

def configure_scheduler() -> AsyncIOScheduler:
    """
    Register all jobs and return the configured scheduler (not yet started).
    Call scheduler.start() inside the FastAPI lifespan.
    """
    # Bi-monthly cycle reminders — 1st of Jan/Mar/May/Jul/Sep/Nov at 08:00 UTC
    scheduler.add_job(
        send_cycle_reminders,
        trigger=CronTrigger(month="1,3,5,7,9,11", day="1", hour="8", minute="0"),
        id="send_cycle_reminders",
        name="Bi-monthly cycle reminder emails",
        replace_existing=True,
        misfire_grace_time=3600,   # tolerate up to 1 h of missed fires
    )

    # Daily JWT blacklist cleanup at 03:00 UTC
    scheduler.add_job(
        purge_expired_tokens,
        trigger=CronTrigger(hour="3", minute="0"),
        id="purge_expired_tokens",
        name="Purge expired JWT blacklist entries",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    return scheduler

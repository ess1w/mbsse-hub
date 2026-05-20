"""
Celery tasks for automated submission reminders.

Logic:
  - 14 days before deadline  → "deadline_approaching" email to all non-submitters
  - 7 days before deadline   → second "deadline_approaching" email
  - 1 day before deadline    → final warning
  - Day after deadline       → "overdue" email

Each task is idempotent: it checks the reminders table to avoid re-sending
the same type of reminder for the same org × period.
"""
import asyncio
from datetime import date, timedelta, timezone, datetime

from app.tasks.celery_app import celery
from app.core.config import get_settings

settings = get_settings()

REMINDER_WINDOWS = [14, 7, 1]   # days before deadline


def _run_async(coro):
    """Run an async function inside a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery.task(name="app.tasks.reminders.check_and_queue_reminders", bind=True, max_retries=3)
def check_and_queue_reminders(self):
    """
    Called daily. Finds the active reporting period, identifies non-submitters,
    and queues individual send_reminder tasks at the right intervals.
    """
    _run_async(_check_and_queue())


async def _check_and_queue():
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.reporting_period import ReportingPeriod
    from app.models.organisation import Organisation
    from app.models.submission import Submission
    from app.models.reminder import Reminder

    today = date.today()

    async with AsyncSessionLocal() as db:
        period = await db.scalar(
            select(ReportingPeriod).where(ReportingPeriod.is_active == True)
        )
        if not period:
            return

        days_to_deadline = (period.deadline - today).days

        # Determine which reminder type to send today
        if days_to_deadline == 1:
            reminder_type = "deadline_approaching"
        elif days_to_deadline in REMINDER_WINDOWS:
            reminder_type = "deadline_approaching"
        elif days_to_deadline == -1:   # one day past deadline
            reminder_type = "overdue"
        else:
            return   # not a reminder day

        # Get all active orgs
        orgs = (await db.scalars(
            select(Organisation).where(Organisation.is_active == True)
        )).all()

        submitted_org_ids = set(
            (await db.scalars(
                select(Submission.organisation_id).where(
                    Submission.reporting_period_id == period.id,
                    Submission.status.in_(["submitted", "verified"]),
                )
            )).all()
        )

        for org in orgs:
            if org.id in submitted_org_ids:
                continue   # already submitted — skip
            if not org.focal_email:
                continue   # no contact email

            # Idempotency: skip if same type already sent for this org × period
            already_sent = await db.scalar(
                select(Reminder).where(
                    Reminder.organisation_id == org.id,
                    Reminder.reporting_period_id == period.id,
                    Reminder.reminder_type == reminder_type,
                    Reminder.status == "sent",
                )
            )
            if already_sent:
                continue

            # Log the pending reminder, then queue the actual email
            reminder = Reminder(
                reporting_period_id=period.id,
                organisation_id=org.id,
                sent_to_email=org.focal_email,
                reminder_type=reminder_type,
                status="pending",
                scheduled_for=datetime.now(timezone.utc),
            )
            db.add(reminder)
            await db.flush()

            # Fire-and-forget the email task
            send_reminder_email.delay(
                reminder_id=str(reminder.id),
                org_name=org.name,
                focal_email=org.focal_email,
                focal_name=org.focal_name or "Partner",
                period_label=period.label,
                deadline=period.deadline.isoformat(),
                reminder_type=reminder_type,
                days_to_deadline=days_to_deadline,
            )

        await db.commit()


@celery.task(
    name="app.tasks.reminders.send_reminder_email",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min between retries
)
def send_reminder_email(
    self,
    reminder_id: str,
    org_name: str,
    focal_email: str,
    focal_name: str,
    period_label: str,
    deadline: str,
    reminder_type: str,
    days_to_deadline: int,
):
    _run_async(_do_send_email(
        reminder_id, org_name, focal_email, focal_name,
        period_label, deadline, reminder_type, days_to_deadline,
    ))


async def _do_send_email(
    reminder_id, org_name, focal_email, focal_name,
    period_label, deadline, reminder_type, days_to_deadline,
):
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.models.reminder import Reminder
    from app.services.email import send_email

    subject, body = _build_email(
        org_name, focal_name, period_label, deadline,
        reminder_type, days_to_deadline,
    )

    async with AsyncSessionLocal() as db:
        reminder = await db.get(Reminder, reminder_id)
        if not reminder:
            return
        try:
            await send_email(to=focal_email, subject=subject, html_body=body)
            reminder.status = "sent"
            reminder.sent_at = datetime.now(timezone.utc)
        except Exception as exc:
            reminder.status = "failed"
            reminder.error_message = str(exc)
        await db.commit()


def _build_email(
    org_name, focal_name, period_label, deadline,
    reminder_type, days_to_deadline,
) -> tuple[str, str]:
    hub_url = f"{settings.frontend_url}/form"

    if reminder_type == "overdue":
        subject = f"[MBSSE Hub] OVERDUE: {period_label} report not submitted"
        urgency = "Your report is now <strong>overdue</strong>."
        cta = "Please submit immediately to avoid being flagged."
    elif days_to_deadline == 1:
        subject = f"[MBSSE Hub] FINAL REMINDER: Report due tomorrow — {period_label}"
        urgency = "Your report is due <strong>tomorrow</strong>."
        cta = "Please submit today."
    else:
        subject = f"[MBSSE Hub] Reminder: {period_label} report due in {days_to_deadline} days"
        urgency = f"Your report is due in <strong>{days_to_deadline} days</strong> ({deadline})."
        cta = "Please log in and complete your submission."

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;color:#1a1a2e">
      <div style="background:#1F5C99;padding:16px 24px;border-radius:8px 8px 0 0">
        <span style="color:#fff;font-size:16px;font-weight:600">MBSSE School Safety Coordination Hub</span>
      </div>
      <div style="background:#fff;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
        <p>Dear {focal_name},</p>
        <p>This is a reminder that <strong>{org_name}</strong> has not yet submitted
           the activity report for the <strong>{period_label}</strong> period.</p>
        <p>{urgency} {cta}</p>
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


@celery.task(name="app.tasks.reminders.purge_expired_tokens")
def purge_expired_tokens():
    """Delete JWT blacklist entries whose expiry has passed."""
    _run_async(_do_purge())


async def _do_purge():
    from sqlalchemy import delete
    from app.db.session import AsyncSessionLocal
    from app.models.token_blacklist import TokenBlacklist
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        await db.commit()

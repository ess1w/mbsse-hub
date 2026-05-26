"""
Reminder management endpoints.

  POST /reminders/send-bulk   — admin: trigger immediate reminder send
  GET  /reminders/            — admin: list reminder log
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.reminder import Reminder
from app.models.user import User

router = APIRouter(prefix="/reminders", tags=["reminders"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class BulkSendResult(BaseModel):
    sent: int
    message: str


class ReminderOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    organisation_id: UUID
    reporting_period_id: UUID
    sent_to_email: str
    reminder_type: str
    status: str
    error_message: str | None
    sent_at: object | None       # datetime, serialised as ISO string


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/send-bulk", response_model=BulkSendResult)
async def send_bulk_reminders(
    user: User = Depends(require_admin),
):
    """
    Admin-only: immediately run the same logic as the scheduled cycle-reminder
    job and return the number of emails sent.

    Safe to call multiple times — idempotent (each org×period pair is only
    emailed once; already-sent reminders are skipped).
    """
    from app.scheduler import send_cycle_reminders

    sent = await send_cycle_reminders()
    return BulkSendResult(
        sent=sent,
        message=(
            f"{sent} reminder(s) sent."
            if sent
            else "No new reminders to send (all partners already notified or no active period)."
        ),
    )


@router.get("/", response_model=list[ReminderOut])
async def list_reminders(
    period_id: UUID | None = None,
    org_id: UUID | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Admin-only: browse reminder log, optionally filtered."""
    q = select(Reminder).order_by(Reminder.created_at.desc())
    if period_id:
        q = q.where(Reminder.reporting_period_id == period_id)
    if org_id:
        q = q.where(Reminder.organisation_id == org_id)
    if status:
        q = q.where(Reminder.status == status)

    results = (await db.scalars(q.limit(200))).all()
    return results

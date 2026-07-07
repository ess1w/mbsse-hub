"""
Reporting period management.

  GET    /api/v1/reporting-periods           → list all periods (any authenticated user)
  POST   /api/v1/reporting-periods           → create a period (admin)
  POST   /api/v1/reporting-periods/{id}/activate → make it the active period (admin)
  DELETE /api/v1/reporting-periods/{id}      → delete a period with no submissions (admin)
"""
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_any
from app.db.session import get_db
from app.models.reporting_period import ReportingPeriod
from app.models.submission import Submission
from app.models.user import User
from app.services.audit import log_action

router = APIRouter(prefix="/reporting-periods", tags=["reporting-periods"])


class PeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    label: str
    start_date: date
    end_date: date
    deadline: date
    is_active: bool


class PeriodCreate(BaseModel):
    label: str
    start_date: date
    end_date: date
    deadline: date
    is_active: bool = False


@router.get("", response_model=list[PeriodOut])
async def list_periods(db: AsyncSession = Depends(get_db), _: User = Depends(require_any)):
    rows = (await db.scalars(
        select(ReportingPeriod).order_by(ReportingPeriod.start_date.desc())
    )).all()
    return rows


async def _deactivate_all(db: AsyncSession) -> None:
    await db.execute(update(ReportingPeriod).values(is_active=False))


@router.post("", response_model=PeriodOut, status_code=201)
async def create_period(
    body: PeriodCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if body.end_date < body.start_date:
        raise HTTPException(status_code=422, detail="End date must be on or after start date")
    if await db.scalar(select(ReportingPeriod.id).where(ReportingPeriod.label == body.label)):
        raise HTTPException(status_code=409, detail="A period with this label already exists")

    if body.is_active:
        await _deactivate_all(db)

    period = ReportingPeriod(
        label=body.label.strip(), start_date=body.start_date,
        end_date=body.end_date, deadline=body.deadline, is_active=body.is_active,
    )
    db.add(period)
    await db.flush()
    await log_action(db, admin, "reporting_period.create", "reporting_period", period.id)
    return period


@router.post("/{period_id}/activate", response_model=PeriodOut)
async def activate_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    period = await db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    await _deactivate_all(db)
    period.is_active = True
    await db.flush()
    await log_action(db, admin, "reporting_period.activate", "reporting_period", period.id)
    return period


@router.delete("/{period_id}", status_code=204)
async def delete_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    period = await db.get(ReportingPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Reporting period not found")
    has_subs = await db.scalar(
        select(Submission.id).where(Submission.reporting_period_id == period_id).limit(1)
    )
    if has_subs:
        raise HTTPException(status_code=409, detail="Cannot delete a period that has submissions")
    await log_action(db, admin, "reporting_period.delete", "reporting_period", period_id)
    await db.delete(period)

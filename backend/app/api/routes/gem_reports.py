"""
GEM Coordinator Monthly Report routes.

Permission matrix:
  gem_coordinator → create/update own draft reports; read own reports
  admin           → full CRUD; patch status
  viewer          → read all reports
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_admin, require_any
from app.db.session import get_db
from app.models.gem_report import GemReport, GemReportActivity, GemReportKeyMessage
from app.models.location import District
from app.models.user import User
from app.schemas.gem_report import GemReportIn, GemReportListItem, GemReportOut
from app.services.audit import log_action

router = APIRouter(prefix="/gem-reports", tags=["gem-reports"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_gem_or_admin(user: User) -> None:
    if user.role not in ('gem_coordinator', 'admin'):
        raise HTTPException(status_code=403, detail="GEM Coordinator or Admin access required")


def _require_read_access(user: User) -> None:
    if user.role not in ('gem_coordinator', 'admin', 'viewer', 'gem_district_officer'):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def _require_officer_or_admin(user: User) -> None:
    if user.role not in ('gem_district_officer', 'admin'):
        raise HTTPException(status_code=403, detail="GEM District Officer or Admin access required")


async def _get_or_404(report_id: UUID, db: AsyncSession) -> GemReport:
    report = await db.scalar(
        select(GemReport)
        .options(
            selectinload(GemReport.activities),
            selectinload(GemReport.key_messages),
            selectinload(GemReport.district),
        )
        .where(GemReport.id == report_id)
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _check_ownership(user: User, report: GemReport) -> None:
    """GEM coordinators may only access their own reports; GEM district officers
    may only access reports for their assigned district."""
    if user.role == 'gem_coordinator' and report.submitted_by != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if user.role == 'gem_district_officer' and report.district_id != user.district_id:
        raise HTTPException(status_code=403, detail="Access denied")


def _build_out(report: GemReport) -> GemReportOut:
    """Assemble GemReportOut from ORM object."""
    activities = [a.activity for a in report.activities]
    activity_other = next(
        (a.activity_other for a in report.activities if a.activity == 'Other'), None
    )
    messages = [m.message for m in report.key_messages]
    message_other = next(
        (m.message_other for m in report.key_messages if m.message == 'Other'), None
    )
    return GemReportOut(
        id=report.id,
        reporting_month=report.reporting_month,
        district_id=report.district_id,
        district_name=report.district.district_name if report.district else None,
        coordinator_name=report.coordinator_name,
        schools_covered=report.schools_covered,
        activities_conducted=activities,
        activity_other_text=activity_other,
        total_activities=report.total_activities,
        impl_status=report.impl_status,
        impl_reason=report.impl_reason,
        impl_reason_other=report.impl_reason_other,
        total_participants=report.total_participants,
        girls_reached=report.girls_reached,
        boys_reached=report.boys_reached,
        teachers_parents_community=report.teachers_parents_community,
        teenage_girls=report.teenage_girls,
        children_disability=report.children_disability,
        functional_clubs=report.functional_clubs,
        srgbv_referrals=report.srgbv_referrals,
        key_messages=messages,
        key_message_other_text=message_other,
        main_challenge=report.main_challenge,
        status=report.status,
        submitted_at=report.submitted_at,
        created_at=report.created_at,
        submitted_by=report.submitted_by,
    )


def _apply_payload(report: GemReport, payload: GemReportIn) -> None:
    """Write scalar fields from payload onto an ORM instance."""
    report.reporting_month = payload.reporting_month
    report.district_id = payload.district_id
    report.coordinator_name = payload.coordinator_name
    report.schools_covered = payload.schools_covered
    report.total_activities = payload.total_activities
    report.impl_status = payload.impl_status
    report.impl_reason = payload.impl_reason
    report.impl_reason_other = payload.impl_reason_other
    report.total_participants = payload.total_participants
    report.girls_reached = payload.girls_reached
    report.boys_reached = payload.boys_reached
    report.teachers_parents_community = payload.teachers_parents_community
    report.teenage_girls = payload.teenage_girls
    report.children_disability = payload.children_disability
    report.functional_clubs = payload.functional_clubs
    report.srgbv_referrals = payload.srgbv_referrals
    report.main_challenge = payload.main_challenge


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[GemReportListItem])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_read_access(user)

    q = select(GemReport).options(selectinload(GemReport.district))

    # GEM coordinators only see their own reports
    if user.role == 'gem_coordinator':
        q = q.where(GemReport.submitted_by == user.id)
    # GEM district officers only see submitted/reviewed reports for their district
    elif user.role == 'gem_district_officer':
        q = q.where(
            GemReport.district_id == user.district_id,
            GemReport.status.in_(['submitted', 'reviewed']),
        )

    q = q.order_by(GemReport.reporting_month.desc())
    rows = (await db.scalars(q)).all()

    return [
        GemReportListItem(
            id=r.id,
            reporting_month=r.reporting_month,
            district_name=r.district.district_name if r.district else None,
            coordinator_name=r.coordinator_name,
            schools_covered=r.schools_covered,
            total_participants=r.total_participants,
            status=r.status,
            submitted_at=r.submitted_at,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("", response_model=GemReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: GemReportIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_gem_or_admin(user)

    # Verify district exists
    district = await db.get(District, payload.district_id)
    if not district:
        raise HTTPException(status_code=400, detail="District not found")

    report = GemReport(submitted_by=user.id)
    _apply_payload(report, payload)
    db.add(report)
    await db.flush()  # get report.id before adding children

    # Junction rows — activities
    for act in payload.activities_conducted:
        db.add(GemReportActivity(
            report_id=report.id,
            activity=act,
            activity_other=payload.activity_other_text if act == 'Other' else None,
        ))

    # Junction rows — key messages
    for msg in payload.key_messages:
        db.add(GemReportKeyMessage(
            report_id=report.id,
            message=msg,
            message_other=payload.key_message_other_text if msg == 'Other' else None,
        ))

    await db.commit()
    await log_action(db, user, 'gem_report.create', 'gem_report', report.id)

    return _build_out(await _get_or_404(report.id, db))


@router.get("/{report_id}", response_model=GemReportOut)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_read_access(user)
    report = await _get_or_404(report_id, db)
    _check_ownership(user, report)
    return _build_out(report)


@router.put("/{report_id}", response_model=GemReportOut)
async def update_report(
    report_id: UUID,
    payload: GemReportIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_gem_or_admin(user)
    report = await _get_or_404(report_id, db)
    _check_ownership(user, report)

    if report.status == 'submitted' and user.role != 'admin':
        raise HTTPException(status_code=400, detail="Cannot edit a submitted report")

    # Verify district
    district = await db.get(District, payload.district_id)
    if not district:
        raise HTTPException(status_code=400, detail="District not found")

    _apply_payload(report, payload)

    # Replace junction rows
    for a in list(report.activities):
        await db.delete(a)
    for m in list(report.key_messages):
        await db.delete(m)
    await db.flush()

    for act in payload.activities_conducted:
        db.add(GemReportActivity(
            report_id=report.id,
            activity=act,
            activity_other=payload.activity_other_text if act == 'Other' else None,
        ))
    for msg in payload.key_messages:
        db.add(GemReportKeyMessage(
            report_id=report.id,
            message=msg,
            message_other=payload.key_message_other_text if msg == 'Other' else None,
        ))

    await db.commit()
    await log_action(db, user, 'gem_report.update', 'gem_report', report.id)

    return _build_out(await _get_or_404(report.id, db))


@router.post("/{report_id}/submit", response_model=GemReportOut)
async def submit_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_gem_or_admin(user)
    report = await _get_or_404(report_id, db)
    _check_ownership(user, report)

    if report.status == 'submitted':
        raise HTTPException(status_code=400, detail="Report already submitted")

    report.status = 'submitted'
    report.submitted_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, user, 'gem_report.submit', 'gem_report', report.id)

    return _build_out(await _get_or_404(report.id, db))


@router.post("/{report_id}/review", response_model=GemReportOut)
async def review_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """GEM district officer (own district) or admin marks a submitted report as reviewed."""
    _require_officer_or_admin(user)
    report = await _get_or_404(report_id, db)
    _check_ownership(user, report)   # officer limited to their district

    if report.status != 'submitted':
        raise HTTPException(status_code=400, detail="Only submitted reports can be reviewed")

    report.status = 'reviewed'
    report.reviewed_by = user.id
    report.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, user, 'gem_report.review', 'gem_report', report.id)

    return _build_out(await _get_or_404(report.id, db))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    report = await _get_or_404(report_id, db)
    await db.delete(report)
    await db.commit()
    await log_action(db, user, 'gem_report.delete', 'gem_report', report_id)

"""
Submission CRUD + file upload.

Permission matrix:
  partner  → create draft for own org; update own drafts; read own submissions
  viewer   → read all submissions (no write)
  admin    → full CRUD + patch status/flag
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin, require_any
from app.db.session import get_db
from app.models.submission import (
    Submission, Activity, OutputIndicators, TrainingByFocusArea, SubmissionLocation,
)
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.models.organisation import Organisation
from app.models.project import Project
from app.models.reporting_period import ReportingPeriod
from app.schemas.submission import (
    ActivitySummary,
    LocationSummary,
    SubmissionAdminPatch,
    SubmissionDetail,
    SubmissionDraft,
    SubmissionOut,
    SubmissionReportIn,
    SubmissionSubmit,
    UploadedFileOut,
)
from app.services.file_storage import store_file
from app.services.audit import log_action

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _check_partner_owns(user: User, submission: Submission) -> None:
    """Partners may only access their own organisation's submissions."""
    if user.role == "partner" and submission.org_id != user.organisation_id:
        raise HTTPException(status_code=403, detail="Access denied")


async def _get_or_404(submission_id: UUID, db: AsyncSession) -> Submission:
    sub = await db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


async def _enriched_out(submission_id: UUID, db: AsyncSession) -> SubmissionOut:
    """Re-load a submission with relationships and build the enriched response.

    A full SELECT (rather than a partial refresh) ensures every scalar column
    is freshly loaded, avoiding lazy-load/MissingGreenlet errors during
    Pydantic serialization.
    """
    s = (
        await db.scalars(
            select(Submission)
            .options(
                joinedload(Submission.organisation),
                joinedload(Submission.reporting_period),
                selectinload(Submission.activities),
            )
            .where(Submission.id == submission_id)
        )
    ).unique().first()
    obj = SubmissionOut.model_validate(s)
    obj.focus_areas  = sorted({fa for a in s.activities for fa in (a.focus_areas or [])})
    obj.org_name     = s.organisation.org_name if s.organisation else None
    obj.period_label = s.reporting_period.label if s.reporting_period else None
    return obj


# ── List ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[SubmissionOut])
async def list_submissions(
    period_id: UUID | None = None,
    org_id: UUID | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    q = (
        select(Submission)
        .options(
            joinedload(Submission.organisation),
            joinedload(Submission.reporting_period),
            selectinload(Submission.activities),
        )
    )

    # Partners only see their own org
    if user.role == "partner":
        q = q.where(Submission.org_id == user.organisation_id)
    elif org_id:
        q = q.where(Submission.org_id == org_id)

    if period_id:
        q = q.where(Submission.reporting_period_id == period_id)
    if status_filter:
        q = q.where(Submission.status == status_filter)

    result = await db.scalars(q.order_by(Submission.updated_at.desc()))
    subs = result.unique().all()

    # Build enriched response: org name, period label, focus areas (from activities)
    out = []
    for s in subs:
        focus = sorted({fa for a in s.activities for fa in (a.focus_areas or [])})
        obj = SubmissionOut.model_validate(s)
        obj.focus_areas  = focus
        obj.org_name     = s.organisation.org_name if s.organisation else None
        obj.period_label = s.reporting_period.label if s.reporting_period else None
        out.append(obj)
    return out


# ── Submit report (consolidated, submission-level) ────────────────────────────

@router.post("/submit-report", response_model=SubmissionOut, status_code=201)
async def submit_report(
    body: SubmissionReportIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    """Persist a submission-level report from the Reporting Form.

    Resolves the active reporting period and the org's project server-side,
    then upserts a submission for (org, period) and marks it submitted.
    """
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot submit reports")

    # ── Resolve organisation ──────────────────────────────────────────────────
    # Partner → own org; admin → optional body.org_id; else fall back to first
    # org so the prototype works even before every user is linked to one.
    org_id = user.organisation_id or body.org_id
    if not org_id:
        org_id = await db.scalar(select(Organisation.org_id).limit(1))
    if not org_id:
        raise HTTPException(status_code=400, detail="No organisation available to attribute this report to")

    # ── Resolve active reporting period ───────────────────────────────────────
    period_id = await db.scalar(
        select(ReportingPeriod.id).where(ReportingPeriod.is_active.is_(True)).limit(1)
    )
    if not period_id:
        raise HTTPException(status_code=400, detail="No active reporting period configured")

    # ── Resolve or create a project for the org ───────────────────────────────
    project_id = await db.scalar(select(Project.project_id).where(Project.org_id == org_id).limit(1))
    if not project_id:
        org_name = await db.scalar(select(Organisation.org_name).where(Organisation.org_id == org_id))
        title = body.project_title or f"SRGBV Programme — {org_name}"
        proj = Project(org_id=org_id, project_title=title, project_status="Active")
        db.add(proj)
        await db.flush()
        project_id = proj.project_id
    elif body.project_title:
        # Update project title if the partner changed it
        proj = await db.get(Project, project_id)
        if proj:
            proj.project_title = body.project_title

    # ── Upsert submission for (org, period) ───────────────────────────────────
    # Submission-level scalar columns only — activities/districts handled below.
    data = body.model_dump(
        exclude={"org_id", "activities", "districts"}, exclude_unset=True
    )
    from sqlalchemy import delete as sa_delete
    sub = await db.scalar(
        select(Submission).where(
            Submission.org_id == org_id,
            Submission.reporting_period_id == period_id,
        )
    )
    if sub:
        for k, v in data.items():
            setattr(sub, k, v)
        # Remove stale files so a resubmission doesn't accumulate old uploads
        await db.execute(
            sa_delete(UploadedFile).where(UploadedFile.submission_id == sub.id)
        )
    else:
        sub = Submission(
            org_id=org_id,
            project_id=project_id,
            reporting_period_id=period_id,
            **data,
        )
        db.add(sub)

    sub.status = "submitted"
    sub.submitted_by = user.id
    sub.submitted_at = datetime.now(timezone.utc)
    await db.flush()

    # ── Replace activities, indicators, training and locations ────────────────
    # Clean resubmit: drop existing children (DB FKs cascade to indicators/training).
    await db.execute(sa_delete(Activity).where(Activity.submission_id == sub.id))
    await db.execute(
        sa_delete(SubmissionLocation).where(SubmissionLocation.submission_id == sub.id)
    )

    # Section B districts: use the client-supplied list, else the union across activities.
    districts = body.districts or sorted(
        {d for a in body.activities for d in a.districts}
    )
    for d in districts:
        db.add(SubmissionLocation(submission_id=sub.id, district_name=d))

    for a in body.activities:
        act = Activity(
            submission_id=sub.id,
            focus_areas=a.focus_areas,
            focus_area_other=a.focus_area_other,
            objectives=a.objectives,
            tactics=a.tactics,
            districts=a.districts,
            activity_type=a.activity_type,
            intervention_levels=a.intervention_levels,
            activity_title=a.activity_title,
            description=a.description,
            planned_vs_actual=a.planned_vs_actual,
            implementation_status=a.implementation_status,
            start_date=a.start_date,
            end_date=a.end_date,
        )
        db.add(act)
        await db.flush()  # populate act.activity_id

        for ind in a.indicators:
            db.add(OutputIndicators(activity_id=act.activity_id, **ind.model_dump()))
        for tr in a.training:
            db.add(TrainingByFocusArea(activity_id=act.activity_id, **tr.model_dump()))

    await db.flush()

    await log_action(db, user, "submission.submit_report", "submission", sub.id)
    return await _enriched_out(sub.id, db)


# ── Create (draft) ────────────────────────────────────────────────────────────

@router.post("/", response_model=SubmissionOut, status_code=201)
async def create_submission(
    body: SubmissionDraft,
    project_id: UUID,
    reporting_period_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot create submissions")

    org_id = user.organisation_id
    if user.role == "admin":
        # admin can create on behalf of any org — org_id comes from project
        from app.models.project import Project
        proj = await db.get(Project, project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        org_id = proj.organisation_id

    # Check uniqueness
    existing = await db.scalar(
        select(Submission).where(
            Submission.organisation_id == org_id,
            Submission.project_id == project_id,
            Submission.reporting_period_id == reporting_period_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Submission already exists for this period")

    data = body.model_dump(exclude_none=True)
    focus_areas = data.pop("focus_areas", [])

    sub = Submission(
        organisation_id=org_id,
        project_id=project_id,
        reporting_period_id=reporting_period_id,
        submitted_by=user.id,
        status="draft",
        **data,
    )
    db.add(sub)
    await db.flush()  # get sub.id

    for fa in focus_areas:
        db.add(SubmissionFocusArea(submission_id=sub.id, focus_area=fa))

    await log_action(db, user, "submission.create", "submission", sub.id)
    await db.refresh(sub, ["focus_areas"])
    out = SubmissionOut.model_validate(sub)
    out.focus_areas = focus_areas
    return out


# ── Read ──────────────────────────────────────────────────────────────────────

@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    s = (
        await db.scalars(
            select(Submission)
            .options(
                joinedload(Submission.organisation),
                joinedload(Submission.reporting_period),
                selectinload(Submission.activities).selectinload(Activity.output_indicators),
                selectinload(Submission.locations),
                selectinload(Submission.files),
            )
            .where(Submission.id == submission_id)
        )
    ).unique().first()
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    _check_partner_owns(user, s)

    out = SubmissionDetail.model_validate(s)
    out.org_name     = s.organisation.org_name if s.organisation else None
    out.period_label = s.reporting_period.label if s.reporting_period else None
    out.focus_areas  = sorted({fa for a in s.activities for fa in (a.focus_areas or [])})

    def _sum(rows, attr):
        return sum((getattr(r, attr) or 0) for r in rows)

    out.activities = [
        ActivitySummary(
            activity_title=a.activity_title,
            activity_type=a.activity_type,
            implementation_status=a.implementation_status,
            focus_areas=a.focus_areas or [],
            objectives=a.objectives or [],
            # Aggregate across the per-district output_indicators rows
            students_f=_sum(a.output_indicators, "students_inschool_f"),
            students_m=_sum(a.output_indicators, "students_inschool_m"),
            teachers_f=_sum(a.output_indicators, "teachers_f"),
            teachers_m=_sum(a.output_indicators, "teachers_m"),
            community_f=_sum(a.output_indicators, "community_members_f"),
            community_m=_sum(a.output_indicators, "community_members_m"),
            schools_total=(
                _sum(a.output_indicators, "schools_primary")
                + _sum(a.output_indicators, "schools_jss")
                + _sum(a.output_indicators, "schools_sss")
            ),
        )
        for a in s.activities
    ]
    out.locations = [LocationSummary.model_validate(loc) for loc in s.locations]
    out.files = [UploadedFileOut.model_validate(f) for f in s.files]
    return out


# ── Save draft (partial update) ────────────────────────────────────────────────

@router.patch("/{submission_id}/draft", response_model=SubmissionOut)
async def save_draft(
    submission_id: UUID,
    body: SubmissionDraft,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    sub = await _get_or_404(submission_id, db)
    _check_partner_owns(user, sub)
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot edit submissions")
    if sub.status == "submitted" and user.role == "partner":
        raise HTTPException(status_code=409, detail="Cannot edit a submitted report")

    data = body.model_dump(exclude_none=True)
    focus_areas = data.pop("focus_areas", None)

    for k, v in data.items():
        setattr(sub, k, v)

    if focus_areas is not None:
        # Replace junction rows
        await db.execute(
            SubmissionFocusArea.__table__.delete().where(
                SubmissionFocusArea.submission_id == sub.id
            )
        )
        for fa in focus_areas:
            db.add(SubmissionFocusArea(submission_id=sub.id, focus_area=fa))

    await log_action(db, user, "submission.draft_save", "submission", sub.id)
    await db.refresh(sub, ["focus_areas"])
    out = SubmissionOut.model_validate(sub)
    out.focus_areas = [fa.focus_area for fa in sub.focus_areas]
    return out


# ── Final submit ─────────────────────────────────────────────────────────────

@router.post("/{submission_id}/submit", response_model=SubmissionOut)
async def submit_submission(
    submission_id: UUID,
    body: SubmissionSubmit,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    sub = await _get_or_404(submission_id, db)
    _check_partner_owns(user, sub)
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot submit reports")
    if sub.status not in ("draft",):
        raise HTTPException(status_code=409, detail="Only drafts can be submitted")

    data = body.model_dump()
    focus_areas = data.pop("focus_areas", [])

    for k, v in data.items():
        setattr(sub, k, v)
    sub.status = "submitted"
    sub.submitted_at = datetime.now(timezone.utc)
    sub.submitted_by = user.id

    # Replace focus areas
    await db.execute(
        SubmissionFocusArea.__table__.delete().where(
            SubmissionFocusArea.submission_id == sub.id
        )
    )
    for fa in focus_areas:
        db.add(SubmissionFocusArea(submission_id=sub.id, focus_area=fa))

    await log_action(db, user, "submission.submit", "submission", sub.id)
    await db.refresh(sub, ["focus_areas"])
    out = SubmissionOut.model_validate(sub)
    out.focus_areas = focus_areas
    return out


# ── Admin patch (status / flag) ───────────────────────────────────────────────

@router.patch("/{submission_id}/admin", response_model=SubmissionOut)
async def admin_patch(
    submission_id: UUID,
    body: SubmissionAdminPatch,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    sub = await _get_or_404(submission_id, db)
    if body.status:
        sub.status = body.status
        if body.status == "verified":
            sub.verified_by = user.id
            sub.verified_at = datetime.now(timezone.utc)
    if body.review_flag is not None:
        sub.review_flag = body.review_flag
    if body.review_notes is not None:
        sub.review_notes = body.review_notes

    await log_action(db, user, "submission.admin_patch", "submission", sub.id,
                     diff=body.model_dump(exclude_none=True))
    await db.flush()
    return await _enriched_out(sub.id, db)


# ── File upload ───────────────────────────────────────────────────────────────

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOC_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_PHOTO_BYTES = 5 * 1024 * 1024    # 5 MB
MAX_DOC_BYTES   = 10 * 1024 * 1024   # 10 MB


@router.post("/{submission_id}/files", status_code=201)
async def upload_file(
    submission_id: UUID,
    file_kind: str,            # 'photo' | 'document'
    upload: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    sub = await _get_or_404(submission_id, db)
    _check_partner_owns(user, sub)
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot upload files")

    if file_kind not in ("photo", "document"):
        raise HTTPException(status_code=422, detail="file_kind must be 'photo' or 'document'")

    # MIME validation
    if file_kind == "photo" and upload.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(status_code=415, detail="Only JPG, PNG, WEBP photos allowed")
    if file_kind == "document" and upload.content_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, Word, Excel documents allowed")

    content = await upload.read()
    max_bytes = MAX_PHOTO_BYTES if file_kind == "photo" else MAX_DOC_BYTES
    if len(content) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File exceeds {mb} MB limit")

    try:
        stored_key, storage_url = await store_file(
            content=content,
            original_filename=upload.filename,
            submission_id=str(submission_id),
            file_kind=file_kind,
            mime_type=upload.content_type or "application/octet-stream",
        )
    except Exception as exc:
        logger.error("File storage failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"File storage error: {exc}")

    file_rec = UploadedFile(
        submission_id=submission_id,
        uploaded_by=user.id,
        file_kind=file_kind,
        original_filename=upload.filename,
        stored_key=stored_key,
        file_size_bytes=len(content),
        mime_type=upload.content_type,
        storage_url=storage_url,
    )
    db.add(file_rec)
    await log_action(db, user, "file.upload", "uploaded_file", file_rec.id)
    return {"id": str(file_rec.id), "filename": upload.filename, "url": storage_url}

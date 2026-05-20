"""
Submission CRUD + file upload.

Permission matrix:
  partner  → create draft for own org; update own drafts; read own submissions
  viewer   → read all submissions (no write)
  admin    → full CRUD + patch status/flag
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin, require_any
from app.db.session import get_db
from app.models.submission import Submission
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.schemas.submission import (
    SubmissionAdminPatch,
    SubmissionDetail,
    SubmissionDraft,
    SubmissionOut,
    SubmissionSubmit,
)
from app.services.file_storage import store_file
from app.services.audit import log_action

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _check_partner_owns(user: User, submission: Submission) -> None:
    """Partners may only access their own organisation's submissions."""
    if user.role == "partner" and submission.organisation_id != user.organisation_id:
        raise HTTPException(status_code=403, detail="Access denied")


async def _get_or_404(submission_id: UUID, db: AsyncSession) -> Submission:
    sub = await db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return sub


# ── List ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[SubmissionOut])
async def list_submissions(
    period_id: UUID | None = None,
    org_id: UUID | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    q = select(Submission)

    # Partners only see their own org
    if user.role == "partner":
        q = q.where(Submission.organisation_id == user.organisation_id)
    elif org_id:
        q = q.where(Submission.organisation_id == org_id)

    if period_id:
        q = q.where(Submission.reporting_period_id == period_id)
    if status_filter:
        q = q.where(Submission.status == status_filter)

    result = await db.scalars(q.order_by(Submission.updated_at.desc()))
    subs = result.all()

    # Attach focus_areas from junction table
    out = []
    for s in subs:
        await db.refresh(s, ["focus_areas"])
        obj = SubmissionOut.model_validate(s)
        obj.focus_areas = [fa.focus_area for fa in s.focus_areas]
        out.append(obj)
    return out


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
    sub = await _get_or_404(submission_id, db)
    _check_partner_owns(user, sub)
    await db.refresh(sub, ["focus_areas"])
    out = SubmissionDetail.model_validate(sub)
    out.focus_areas = [fa.focus_area for fa in sub.focus_areas]
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
    await db.refresh(sub, ["focus_areas"])
    out = SubmissionOut.model_validate(sub)
    out.focus_areas = [fa.focus_area for fa in sub.focus_areas]
    return out


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

    stored_key, storage_url = await store_file(
        content=content,
        original_filename=upload.filename,
        submission_id=str(submission_id),
        file_kind=file_kind,
    )

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

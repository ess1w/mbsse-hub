"""
SLA document upload + admin review.

  POST   /api/v1/organisations/{org_id}/sla   → partner uploads SLA (PDF/Word)
  GET    /api/v1/organisations/{org_id}/sla   → list documents for an org
  PATCH  /api/v1/sla-documents/{doc_id}       → admin approve / reject
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin, require_any
from app.db.session import get_db
from app.models.organisation import Organisation
from app.models.sla_document import SlaDocument
from app.models.user import User
from app.schemas.sla import SlaDocumentOut, SlaReviewPatch
from app.services.audit import log_action
from app.services.file_storage import store_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sla"])

ALLOWED_SLA_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_SLA_BYTES = 10 * 1024 * 1024  # 10 MB


def _check_org_access(user: User, org_id: UUID) -> None:
    if user.role == "partner" and user.organisation_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.post("/organisations/{org_id}/sla", response_model=SlaDocumentOut, status_code=201)
async def upload_sla(
    org_id: UUID,
    upload: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    if user.role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot upload SLA documents")
    _check_org_access(user, org_id)

    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if upload.content_type not in ALLOWED_SLA_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF or Word documents are allowed")

    content = await upload.read()
    if len(content) > MAX_SLA_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    try:
        stored_key, storage_url = await store_file(
            content=content,
            original_filename=upload.filename,
            submission_id=str(org_id),
            file_kind="document",
            mime_type=upload.content_type or "application/octet-stream",
            prefix="sla",
        )
    except Exception as exc:
        logger.error("SLA storage failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"File storage error: {exc}")

    doc = SlaDocument(
        org_id=org_id,
        uploaded_by=user.id,
        original_filename=upload.filename,
        stored_key=stored_key,
        file_size_bytes=len(content),
        mime_type=upload.content_type,
        storage_url=storage_url,
        status="pending",
    )
    db.add(doc)
    await db.flush()
    await log_action(db, user, "sla.upload", "sla_document", doc.id)
    return SlaDocumentOut.model_validate(doc)


@router.get("/organisations/{org_id}/sla", response_model=list[SlaDocumentOut])
async def list_sla(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any),
):
    _check_org_access(user, org_id)
    rows = (
        await db.scalars(
            select(SlaDocument)
            .where(SlaDocument.org_id == org_id)
            .order_by(SlaDocument.created_at.desc())
        )
    ).all()
    return [SlaDocumentOut.model_validate(r) for r in rows]


@router.patch("/sla-documents/{doc_id}", response_model=SlaDocumentOut)
async def review_sla(
    doc_id: UUID,
    body: SlaReviewPatch,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    doc = await db.get(SlaDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="SLA document not found")

    doc.status = body.status
    doc.review_notes = body.review_notes
    doc.reviewed_by = user.id
    doc.reviewed_at = datetime.now(timezone.utc)

    # Approving the SLA marks the organisation's agreement as signed.
    org = await db.get(Organisation, doc.org_id)
    if org and body.status == "approved":
        org.sla_signed = True

    await log_action(db, user, "sla.review", "sla_document", doc.id,
                     diff=body.model_dump())
    await db.flush()
    return SlaDocumentOut.model_validate(doc)

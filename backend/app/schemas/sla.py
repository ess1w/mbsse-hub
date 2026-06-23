"""Schemas for organisation SLA documents."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SlaDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    original_filename: str
    file_size_bytes: int
    mime_type: str | None = None
    storage_url: str | None = None
    status: str
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime


class SlaReviewPatch(BaseModel):
    status: Literal["approved", "rejected"]
    review_notes: str | None = None

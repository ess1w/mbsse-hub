"""
SLA documents — organisation-level Service Level Agreement uploads.

Partners upload an SLA (PDF / Word); admins review and approve or reject.
Approving the latest document flips Organisation.sla_signed = True.
"""
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class SlaDocument(Base):
    __tablename__ = "sla_documents"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id            = Column(UUID(as_uuid=True), ForeignKey("organisations.org_id", ondelete="CASCADE"), nullable=False)
    uploaded_by       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    original_filename = Column(String(255), nullable=False)
    stored_key        = Column(Text, unique=True, nullable=False)
    file_size_bytes   = Column(Integer, nullable=False)
    mime_type         = Column(String(100))
    storage_url       = Column(Text)
    status            = Column(String(20), nullable=False, default="pending")  # pending / approved / rejected
    reviewed_by       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at       = Column(TIMESTAMPTZ)
    review_notes      = Column(Text)
    created_at        = Column(TIMESTAMPTZ, server_default=func.now())

    organisation = relationship("Organisation", backref="sla_documents")

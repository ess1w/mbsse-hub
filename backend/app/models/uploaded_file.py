import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import relationship
from app.models.base import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_kind = Column(String(10), nullable=False)          # 'photo' | 'document'
    original_filename = Column(String(255), nullable=False)
    stored_key = Column(Text, unique=True, nullable=False)  # S3 key or local path
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    storage_url = Column(Text)                              # presigned URL (refreshed on read)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())

    submission = relationship("Submission", back_populates="files")
    uploader = relationship("User", back_populates="uploaded_files")

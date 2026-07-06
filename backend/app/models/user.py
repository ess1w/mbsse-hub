import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False, default="partner")   # admin|viewer|partner|gem_coordinator|gem_district_officer
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.org_id", ondelete="SET NULL"), nullable=True)
    # District assignment — used by gem_district_officer (which district they review)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    must_change_password = Column(Boolean, nullable=False, default=False)
    last_login = Column(TIMESTAMPTZ)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    organisation = relationship("Organisation", back_populates="users")
    district = relationship("District")
    uploaded_files = relationship("UploadedFile", back_populates="uploader")

"""
Organisation Registry — matches Section 5.1 of the data dictionary.
"""
import uuid
from sqlalchemy import Boolean, Column, Date, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class Organisation(Base):
    __tablename__ = "organisations"

    # 5.1 fields (canonical names)
    org_id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_name           = Column(String(200), unique=True, nullable=False)
    org_type           = Column(String(40), nullable=False)          # CSO / UN Agency / Government / Other
    focal_person       = Column(String(120))
    email              = Column(String(254))
    phone              = Column(String(30))
    sla_signed         = Column(Boolean, nullable=False, default=False)
    registration_date  = Column(Date, server_default=func.current_date())
    status             = Column(String(20), nullable=False, default="Pending")  # Active / Inactive / Pending

    # Extra admin fields (beyond data dictionary, useful for directory display)
    acronym            = Column(String(30))
    districts          = Column(ARRAY(String), default=list)  # operational districts for directory
    notes              = Column(Text)

    created_at  = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at  = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    # relationships
    users       = relationship("User", back_populates="organisation")
    projects    = relationship("Project", back_populates="organisation", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="organisation")
    reminders   = relationship("Reminder", back_populates="organisation")

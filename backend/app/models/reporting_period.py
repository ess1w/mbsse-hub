import uuid
from sqlalchemy import Boolean, Column, Date, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import relationship
from app.models.base import Base


class ReportingPeriod(Base):
    __tablename__ = "reporting_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(40), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())

    submissions = relationship("Submission", back_populates="reporting_period")
    reminders = relationship("Reminder", back_populates="reporting_period")

import uuid
from sqlalchemy import Column, ForeignKey, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import relationship
from app.models.base import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporting_period_id = Column(UUID(as_uuid=True), ForeignKey("reporting_periods.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.org_id"), nullable=False)
    sent_to_email = Column(String(254), nullable=False)
    reminder_type = Column(String(30), nullable=False)    # deadline_approaching|overdue|manual
    status = Column(String(10), nullable=False, default="pending")  # pending|sent|failed
    error_message = Column(Text)
    scheduled_for = Column(TIMESTAMPTZ)
    sent_at = Column(TIMESTAMPTZ)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())

    reporting_period = relationship("ReportingPeriod", back_populates="reminders")
    organisation = relationship("Organisation", back_populates="reminders")

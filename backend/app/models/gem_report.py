"""
SQLAlchemy ORM model for GEM Coordinator monthly reports.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Date, ForeignKey, Integer, String, Text,
    TIMESTAMP, Enum as SAEnum, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base

GEM_ACTIVITIES = [
    'School awareness session',
    'School club activity',
    'Community sensitization',
    'Teacher orientation/training',
    'Radio/media awareness',
    'Parent/PTA meeting',
    'Referral pathway orientation',
    'Other',
]

GEM_KEY_MESSAGES = [
    'Bullying prevention',
    'Prevention of sexual harassment',
    'Alternative discipline/no corporal punishment',
    'Referral/reporting pathways',
    'Child rights/safe schools',
    'Teacher code of conduct',
    'Other',
]

GEM_IMPL_STATUSES = ['Fully', 'Partially', 'Not implemented']
GEM_IMPL_REASONS = [
    'Lack of funds', 'Low participation', 'Weather/logistics',
    'School schedule conflict', 'Lack of materials', 'Other',
]


class GemReportActivity(Base):
    __tablename__ = 'gem_report_activities'

    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey('gem_reports.id', ondelete='CASCADE'),
        primary_key=True,
    )
    activity = Column(String(80), primary_key=True)
    activity_other = Column(Text, nullable=True)

    report = relationship('GemReport', back_populates='activities')


class GemReportKeyMessage(Base):
    __tablename__ = 'gem_report_key_messages'

    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey('gem_reports.id', ondelete='CASCADE'),
        primary_key=True,
    )
    message = Column(String(80), primary_key=True)
    message_other = Column(Text, nullable=True)

    report = relationship('GemReport', back_populates='key_messages')


class GemReport(Base):
    __tablename__ = 'gem_reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Section 1
    reporting_month = Column(Date, nullable=False)
    district_id = Column(Integer, ForeignKey('districts.id'), nullable=False)
    coordinator_name = Column(String(120), nullable=False)
    schools_covered = Column(Integer, nullable=False, default=0)

    # Section 2
    total_activities = Column(Integer, nullable=False, default=0)
    impl_status = Column(
        SAEnum(*GEM_IMPL_STATUSES, name='gem_impl_status'),
        nullable=False,
    )
    impl_reason = Column(
        SAEnum(*GEM_IMPL_REASONS, name='gem_impl_reason'),
        nullable=True,
    )
    impl_reason_other = Column(Text, nullable=True)

    # Section 3
    total_participants = Column(Integer, nullable=False, default=0)
    girls_reached = Column(Integer, nullable=False, default=0)
    boys_reached = Column(Integer, nullable=False, default=0)
    teachers_parents_community = Column(Integer, nullable=False, default=0)
    teenage_girls = Column(Integer, nullable=False, default=0)
    children_disability = Column(Integer, nullable=False, default=0)

    # Section 4
    functional_clubs = Column(Integer, nullable=False, default=0)
    srgbv_referrals = Column(Integer, nullable=False, default=0)

    # Section 5
    main_challenge = Column(Text, nullable=True)

    # Status
    status = Column(
        SAEnum('draft', 'submitted', 'reviewed', name='gem_submission_status'),
        nullable=False,
        default='draft',
    )
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Review by a GEM district officer
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    # Relationships
    activities = relationship(
        'GemReportActivity', back_populates='report',
        cascade='all, delete-orphan',
    )
    key_messages = relationship(
        'GemReportKeyMessage', back_populates='report',
        cascade='all, delete-orphan',
    )
    district = relationship('District', lazy='joined')
    submitter = relationship('User', foreign_keys=[submitted_by], lazy='joined')

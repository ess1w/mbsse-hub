"""
Pydantic schemas for GEM Coordinator monthly reports.
"""
from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ── Choice constants (mirrors model.py) ──────────────────────────────────────

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

ImplStatus = Literal['Fully', 'Partially', 'Not implemented']
ImplReason = Literal[
    'Lack of funds', 'Low participation', 'Weather/logistics',
    'School schedule conflict', 'Lack of materials', 'Other',
]
GemStatus = Literal['draft', 'submitted']


# ── Nested activity/message items ─────────────────────────────────────────────

class ActivityItem(BaseModel):
    activity: str
    activity_other: Optional[str] = None


class KeyMessageItem(BaseModel):
    message: str
    message_other: Optional[str] = None


# ── Input schema ──────────────────────────────────────────────────────────────

class GemReportIn(BaseModel):
    # Section 1
    reporting_month: date = Field(..., description="First day of the reporting month, e.g. 2026-06-01")
    district_id: int
    coordinator_name: str = Field(..., min_length=1, max_length=120)
    schools_covered: int = Field(..., ge=0)

    # Section 2
    activities_conducted: list[str] = Field(default_factory=list)
    activity_other_text: Optional[str] = None          # free text when "Other" selected
    total_activities: int = Field(..., ge=0)
    impl_status: ImplStatus
    impl_reason: Optional[ImplReason] = None
    impl_reason_other: Optional[str] = None

    # Section 3
    total_participants: int = Field(0, ge=0)
    girls_reached: int = Field(0, ge=0)
    boys_reached: int = Field(0, ge=0)
    teachers_parents_community: int = Field(0, ge=0)
    teenage_girls: int = Field(0, ge=0)
    children_disability: int = Field(0, ge=0)

    # Section 4
    functional_clubs: int = Field(0, ge=0)
    srgbv_referrals: int = Field(0, ge=0)
    key_messages: list[str] = Field(default_factory=list)
    key_message_other_text: Optional[str] = None

    # Section 5
    main_challenge: Optional[str] = None

    @model_validator(mode='after')
    def reason_required_when_not_fully(self) -> 'GemReportIn':
        if self.impl_status in ('Partially', 'Not implemented') and not self.impl_reason:
            raise ValueError('impl_reason is required when implementation was not fully completed')
        if self.impl_reason == 'Other' and not self.impl_reason_other:
            raise ValueError('impl_reason_other is required when reason is Other')
        return self


# ── Output schema ─────────────────────────────────────────────────────────────

class GemReportOut(BaseModel):
    id: UUID
    reporting_month: date
    district_id: int
    district_name: Optional[str] = None
    coordinator_name: str
    schools_covered: int
    activities_conducted: list[str]
    activity_other_text: Optional[str] = None
    total_activities: int
    impl_status: str
    impl_reason: Optional[str] = None
    impl_reason_other: Optional[str] = None
    total_participants: int
    girls_reached: int
    boys_reached: int
    teachers_parents_community: int
    teenage_girls: int
    children_disability: int
    functional_clubs: int
    srgbv_referrals: int
    key_messages: list[str]
    key_message_other_text: Optional[str] = None
    main_challenge: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime
    submitted_by: Optional[UUID] = None

    model_config = {'from_attributes': True}


class GemReportListItem(BaseModel):
    id: UUID
    reporting_month: date
    district_name: Optional[str] = None
    coordinator_name: str
    schools_covered: int
    total_participants: int
    status: str
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {'from_attributes': True}

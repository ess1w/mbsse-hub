"""
Submission + Activity + SubmissionLocation + OutputIndicators
Matches Sections 5.5, 5.6, 5.7 of the data dictionary.
"""
import uuid
from sqlalchemy import (
    Boolean, Column, Date, Float, ForeignKey, Integer, Numeric, String, Text, TIMESTAMP, func
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class Submission(Base):
    """Top-level bi-monthly report filed by a partner organisation."""
    __tablename__ = "submissions"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id              = Column(UUID(as_uuid=True), ForeignKey("organisations.org_id"), nullable=False)
    project_id          = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    reporting_period_id = Column(UUID(as_uuid=True), ForeignKey("reporting_periods.id"), nullable=False)
    submitted_by        = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    verified_by         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status              = Column(String(20), nullable=False, default="draft")   # draft / submitted / verified

    # Section F — Outcomes
    key_results      = Column(Text)
    observed_changes = Column(Text)
    early_outcomes   = Column(Text)

    # Section G — Financial
    expenditure          = Column(Numeric(14, 2))
    expenditure_currency = Column(String(3), default="USD")
    budget_util          = Column(String(30))

    # Section H — Coordination
    gov_engaged            = Column(Boolean)
    gov_engaged_list       = Column(Text)
    coordination_meetings  = Column(Integer, default=0)
    key_partners           = Column(Text)

    # Section I — Challenges
    challenges  = Column(Text)
    risks       = Column(Text)
    mitigations = Column(Text)

    # Section J — Safeguarding (case data under access control)
    safeguarding_cases  = Column(Boolean, nullable=False, default=False)
    cases_reported      = Column(Integer, default=0)
    cases_referred      = Column(Integer, default=0)
    referral_pathway    = Column(String(120))
    safeguarding_action = Column(Text)

    # Section L — Next period
    planned_activities = Column(Text)
    support_needed     = Column(Text)

    # Section M — Admin review
    review_flag  = Column(String(40))
    review_notes = Column(Text)

    submitted_at = Column(TIMESTAMPTZ)
    verified_at  = Column(TIMESTAMPTZ)
    created_at   = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at   = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    # Relationships
    organisation     = relationship("Organisation", back_populates="submissions")
    project          = relationship("Project", back_populates="submissions")
    reporting_period = relationship("ReportingPeriod", back_populates="submissions")
    activities       = relationship("Activity", back_populates="submission", cascade="all, delete-orphan")
    locations        = relationship("SubmissionLocation", back_populates="submission", cascade="all, delete-orphan")
    files            = relationship("UploadedFile", back_populates="submission", cascade="all, delete-orphan")


class SubmissionLocation(Base):
    """
    Section 5.6 — Submission Locations junction table.
    Each row = one district/chiefdom/school combo covered by the submission.
    """
    __tablename__ = "submission_locations"

    location_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id  = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    district_name  = Column(String(60), nullable=False)
    chiefdom_name  = Column(String(80))
    community_name = Column(String(120))
    school_name    = Column(String(200))
    emis_code      = Column(String(20))
    gps_lat        = Column(Float)
    gps_lon        = Column(Float)

    submission = relationship("Submission", back_populates="locations")


class Activity(Base):
    """
    Section 5.5 — Activity Registry.
    One submission can have multiple activities (multi-activity repeater in Section C/D).
    """
    __tablename__ = "activities"

    activity_id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id        = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)

    # Section C — Classification (all multi-select → ARRAY)
    focus_areas          = Column(ARRAY(String), default=list)   # fa1 … fa8
    focus_area_other     = Column(Text)                          # free text when "8. Other" is selected
    objectives           = Column(ARRAY(String), default=list)   # obj1 / obj2 / obj3
    tactics              = Column(ARRAY(String), default=list)   # tac1 … tac9
    districts            = Column(ARRAY(String), default=list)   # Section C — district(s) this activity covers
    activity_type        = Column(String(80))                    # Training / Safe Space / Awareness / etc.
    intervention_levels  = Column(ARRAY(String), default=list)   # School-based / Community-based / System-level

    # Section D — Implementation details
    activity_title       = Column(String(300))
    description          = Column(Text)
    planned_vs_actual    = Column(String(20))                    # As planned / Modified
    implementation_status = Column(String(20))                   # Not started / Ongoing / Completed / Delayed
    start_date           = Column(Date)
    end_date             = Column(Date)

    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    submission      = relationship("Submission", back_populates="activities")
    # One row per (activity, district). With a single district there is one row.
    output_indicators = relationship("OutputIndicators", back_populates="activity", cascade="all, delete-orphan")
    training_rows     = relationship("TrainingByFocusArea", back_populates="activity", cascade="all, delete-orphan")


class OutputIndicators(Base):
    """
    Section 5.7 — Output Indicators.
    One row per (activity, district). When an activity covers multiple districts
    the partner enters a full indicator set per district; single-district
    activities have one row keyed with district_name = '' (overall).
    """
    __tablename__ = "output_indicators"

    activity_id   = Column(UUID(as_uuid=True), ForeignKey("activities.activity_id", ondelete="CASCADE"), primary_key=True)
    district_name = Column(String(60), primary_key=True, nullable=False, default="")

    # Schools reached by level
    schools_pre_primary = Column(Integer, default=0)
    schools_primary     = Column(Integer, default=0)
    schools_jss         = Column(Integer, default=0)
    schools_sss         = Column(Integer, default=0)

    # School-level SRGBV prevention mechanisms
    schools_with_focal_person          = Column(Integer, default=0)
    schools_with_reporting_protocol    = Column(Integer, default=0)
    schools_with_referral_pathway      = Column(Integer, default=0)
    schools_held_schoolwide_campaign   = Column(Integer, default=0)
    schools_held_peer_led_session      = Column(Integer, default=0)
    schools_with_safe_space            = Column(Integer, default=0)

    # Students — in-school, disaggregated by gender and age
    students_inschool_f          = Column(Integer, default=0)
    students_inschool_m          = Column(Integer, default=0)
    students_inschool_age_10_14  = Column(Integer, default=0)
    students_inschool_age_15_19  = Column(Integer, default=0)
    students_inschool_age_under10 = Column(Integer, default=0)
    students_inschool_age_19_plus = Column(Integer, default=0)

    # Students — out-of-school
    students_oos_f          = Column(Integer, default=0)
    students_oos_m          = Column(Integer, default=0)
    students_oos_age_10_14  = Column(Integer, default=0)
    students_oos_age_15_19  = Column(Integer, default=0)
    students_oos_age_19_plus = Column(Integer, default=0)

    # Students with disability
    students_disability_f = Column(Integer, default=0)
    students_disability_m = Column(Integer, default=0)

    # Vulnerable groups
    pregnant_girls    = Column(Integer, default=0)
    teenage_mothers   = Column(Integer, default=0)
    teenage_fathers   = Column(Integer, default=0)

    # Student engagement with SRGBV mechanisms
    students_used_reporting_mechanism = Column(Integer, default=0)
    students_confident_reporting      = Column(Integer, default=0)

    # Teachers / school staff — totals (per-focus-area breakdown in TrainingByFocusArea)
    teachers_f               = Column(Integer, default=0)
    teachers_m               = Column(Integer, default=0)
    teachers_demonstrated_grp = Column(Integer, default=0)

    # District officials — totals (per-focus-area breakdown in TrainingByFocusArea)
    district_officials_f = Column(Integer, default=0)
    district_officials_m = Column(Integer, default=0)

    # Central government officials — totals (per-focus-area breakdown in TrainingByFocusArea)
    central_officials_f = Column(Integer, default=0)
    central_officials_m = Column(Integer, default=0)

    # Community
    community_members_f    = Column(Integer, default=0)
    community_members_m    = Column(Integer, default=0)
    community_sessions     = Column(Integer, default=0)

    # Policy
    policy_dialogue_events = Column(Integer, default=0)

    activity = relationship("Activity", back_populates="output_indicators")


class TrainingByFocusArea(Base):
    """
    Section E (#6) — Teachers / school staff and Government officials trained,
    disaggregated by focus area (and by district, consistent with the per-district
    output indicators). One row per (activity, district, focus_area, cadre).
    """
    __tablename__ = "training_by_focus_area"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id   = Column(UUID(as_uuid=True), ForeignKey("activities.activity_id", ondelete="CASCADE"), nullable=False)
    district_name = Column(String(60), nullable=False, default="")
    focus_area    = Column(String(120), nullable=False)
    cadre         = Column(String(20), nullable=False)   # teacher / district_official / central_official
    female        = Column(Integer, default=0)
    male          = Column(Integer, default=0)

    activity = relationship("Activity", back_populates="training_rows")

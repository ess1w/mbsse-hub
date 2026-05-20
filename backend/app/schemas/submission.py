"""
Pydantic schemas for the 13-section activity report form.
Each section maps directly to the wireframe pages.
"""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# ── Section C choices ─────────────────────────────────────────────────────────

FOCUS_AREAS = {
    "1. SRGBV Prevention & Response",
    "2. MHPSS",
    "3. School Governance",
    "4. Life Skills / SRH",
    "5. WASH",
    "6. Social Norms",
    "7. Social Protection",
    "8. Other",
}

ACTIVITY_TYPES = {
    "Training / Capacity Building",
    "Community Outreach",
    "Awareness Campaign",
    "Safe Space Activities",
    "Policy / Advocacy",
    "Research / Assessment",
    "Coordination Meeting",
    "Other",
}

OBJECTIVES = {"obj1", "obj2", "obj3"}

TACTICS = {
    "obj1": {
        "Carry Out Nationwide Media Campaigns",
        "Strengthen Peer Education Programs",
        "Conduct School-Based Awareness Campaigns",
    },
    "obj2": {
        "Strengthen Capacity of School Personnel",
        "Establish Safe and Inclusive Learning Environments",
        "Implement Community-Based Monitoring and Engagement",
    },
    "obj3": {
        "Enforce Policy",
        "Strengthen Reporting and Referral Systems",
        "Engage Stakeholders for Sustainability",
    },
}

REFERRAL_PATHWAYS = {
    "Police Family Support Unit (FSU)",
    "One-Stop Centre",
    "Social Welfare Office",
    "Health Facility",
    "Community Child Welfare Committee",
    "Other",
}


# ── Draft / partial save (no required fields) ────────────────────────────────

class SubmissionDraft(BaseModel):
    """Used for auto-save / partial saves. All fields optional."""
    # B
    district_id: int | None = None
    chiefdom_id: int | None = None
    community: str | None = None
    school_id: UUID | None = None

    # C
    focus_areas: list[str] = Field(default_factory=list)
    objective: Literal["obj1", "obj2", "obj3"] | None = None
    tactic: str | None = None
    activity_type: str | None = None
    intervention_level: Literal["School-based", "Community", "System-level"] | None = None

    # D
    activity_title: str | None = Field(None, max_length=300)
    impl_status: Literal["Completed", "Ongoing", "Delayed", "Cancelled"] | None = None
    description: str | None = Field(None, max_length=2000)
    planned_vs_actual: Literal["As planned", "Modified"] | None = None
    activity_start: date | None = None
    activity_end: date | None = None

    # E
    schools_reached: int = Field(0, ge=0)
    teachers_trained: int = Field(0, ge=0)
    students_reached: int = Field(0, ge=0)
    community_sessions: int = Field(0, ge=0)
    safe_spaces_setup: int = Field(0, ge=0)
    srgbv_referrals: int = Field(0, ge=0)
    disagg_female: int = Field(0, ge=0)
    disagg_male: int = Field(0, ge=0)
    age_10_14: int = Field(0, ge=0)
    age_15_19: int = Field(0, ge=0)
    with_disability: int = Field(0, ge=0)
    out_of_school: int = Field(0, ge=0)

    # F
    key_results: str | None = None
    observed_changes: str | None = None
    early_outcomes: str | None = None

    # G
    expenditure: float | None = Field(None, ge=0)
    expenditure_currency: str = "USD"
    budget_util: Literal["On track", "Under-spending", "Over-spending"] | None = None

    # H
    gov_engaged: bool | None = None
    gov_counterpart: str | None = None
    coordination_meetings: int = Field(0, ge=0)
    key_partners: str | None = None

    # I
    challenges: str | None = None
    risks: str | None = None
    mitigations: str | None = None

    # J — Safeguarding (always required on final submit, validated there)
    safeguarding_cases: bool = False
    num_cases: int = Field(0, ge=0)
    referral_pathway: str | None = None
    safeguarding_action: str | None = None

    # L
    planned_activities: str | None = None
    support_needed: str | None = None


# ── Final submit (required fields enforced) ───────────────────────────────────

class SubmissionSubmit(SubmissionDraft):
    """All required fields enforced for final submission."""

    # B — required
    district_id: int
    school_id: UUID

    # C — required
    focus_areas: list[str] = Field(min_length=1)
    objective: Literal["obj1", "obj2", "obj3"]
    tactic: str
    activity_type: str
    intervention_level: Literal["School-based", "Community", "System-level"]

    # D — required
    activity_title: str = Field(min_length=1, max_length=300)
    impl_status: Literal["Completed", "Ongoing", "Delayed", "Cancelled"]
    description: str = Field(min_length=10, max_length=2000)
    activity_start: date
    activity_end: date

    # E — at least one output must be > 0
    # J — safeguarding must be explicitly declared

    @model_validator(mode="after")
    def validate_business_rules(self):
        # 1. Activity dates must be coherent
        if self.activity_end and self.activity_start:
            if self.activity_end < self.activity_start:
                raise ValueError("activity_end must be on or after activity_start")

        # 2. Focus areas must be from the allowed set
        bad = set(self.focus_areas) - FOCUS_AREAS
        if bad:
            raise ValueError(f"Unknown focus areas: {bad}")

        # 3. Tactic must belong to chosen objective
        if self.objective and self.tactic:
            valid_tactics = TACTICS.get(self.objective, set())
            if self.tactic not in valid_tactics:
                raise ValueError(f"Tactic '{self.tactic}' is not valid for {self.objective}")

        # 4. Disaggregation: female + male should not exceed students_reached
        total_gender = self.disagg_female + self.disagg_male
        if self.students_reached and total_gender > self.students_reached:
            raise ValueError(
                "disagg_female + disagg_male cannot exceed students_reached"
            )

        # 5. If gov_engaged, gov_counterpart is required
        if self.gov_engaged and not self.gov_counterpart:
            raise ValueError("gov_counterpart is required when gov_engaged is True")

        # 6. Safeguarding detail required when cases reported
        if self.safeguarding_cases:
            if not self.num_cases or self.num_cases < 1:
                raise ValueError("num_cases must be ≥ 1 when safeguarding_cases is True")
            if not self.referral_pathway:
                raise ValueError("referral_pathway is required when cases are reported")
            if self.referral_pathway not in REFERRAL_PATHWAYS:
                raise ValueError(f"Unknown referral pathway: {self.referral_pathway}")

        return self


# ── Admin-only patch ─────────────────────────────────────────────────────────

class SubmissionAdminPatch(BaseModel):
    status: Literal["draft", "submitted", "verified", "flagged"] | None = None
    review_flag: str | None = None
    review_notes: str | None = None


# ── Response schema ───────────────────────────────────────────────────────────

class SubmissionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    organisation_id: UUID
    project_id: UUID
    reporting_period_id: UUID
    status: str
    activity_title: str | None
    description: str | None
    submitted_at: datetime | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Focus areas come from the junction table
    focus_areas: list[str] = Field(default_factory=list)


class SubmissionDetail(SubmissionOut):
    """Full detail view — includes all 13 sections."""
    district_id: int | None
    chiefdom_id: int | None
    community: str | None
    school_id: UUID | None
    objective: str | None
    tactic: str | None
    activity_type: str | None
    intervention_level: str | None
    impl_status: str | None
    planned_vs_actual: str | None
    activity_start: date | None
    activity_end: date | None
    schools_reached: int
    teachers_trained: int
    students_reached: int
    community_sessions: int
    safe_spaces_setup: int
    srgbv_referrals: int
    disagg_female: int
    disagg_male: int
    age_10_14: int
    age_15_19: int
    with_disability: int
    out_of_school: int
    key_results: str | None
    observed_changes: str | None
    early_outcomes: str | None
    expenditure: float | None
    expenditure_currency: str
    budget_util: str | None
    gov_engaged: bool | None
    gov_counterpart: str | None
    coordination_meetings: int
    key_partners: str | None
    challenges: str | None
    risks: str | None
    mitigations: str | None
    safeguarding_cases: bool
    num_cases: int
    referral_pathway: str | None
    safeguarding_action: str | None
    planned_activities: str | None
    support_needed: str | None
    review_flag: str | None
    review_notes: str | None

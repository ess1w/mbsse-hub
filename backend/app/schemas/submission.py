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


# ── Activity / output-indicator / training payloads (Sections C–E) ────────────

class OutputIndicatorIn(BaseModel):
    """All Section E numeric outputs for one (activity, district)."""
    district_name: str = ""

    # Schools by level
    schools_pre_primary: int = 0
    schools_primary: int = 0
    schools_jss: int = 0
    schools_sss: int = 0
    # School-level SRGBV mechanisms
    schools_with_focal_person: int = 0
    schools_with_reporting_protocol: int = 0
    schools_with_referral_pathway: int = 0
    schools_held_schoolwide_campaign: int = 0
    schools_held_peer_led_session: int = 0
    schools_with_safe_space: int = 0
    # Students — in-school
    students_inschool_f: int = 0
    students_inschool_m: int = 0
    students_inschool_age_10_14: int = 0
    students_inschool_age_15_19: int = 0
    students_inschool_age_under10: int = 0
    # Students — out-of-school
    students_oos_f: int = 0
    students_oos_m: int = 0
    students_oos_age_10_14: int = 0
    students_oos_age_15_19: int = 0
    # Disability & vulnerable groups
    students_disability_f: int = 0
    students_disability_m: int = 0
    pregnant_girls: int = 0
    teenage_mothers: int = 0
    teenage_fathers: int = 0
    # Engagement
    students_used_reporting_mechanism: int = 0
    students_confident_reporting: int = 0
    # Teacher / official totals (per-focus-area detail in `training`)
    teachers_f: int = 0
    teachers_m: int = 0
    teachers_demonstrated_grp: int = 0
    district_officials_f: int = 0
    district_officials_m: int = 0
    central_officials_f: int = 0
    central_officials_m: int = 0
    # Community / policy
    community_members_f: int = 0
    community_members_m: int = 0
    community_sessions: int = 0
    policy_dialogue_events: int = 0


class TrainingRowIn(BaseModel):
    """One row of teacher/official training, by focus area + district + cadre (#6)."""
    district_name: str = ""
    focus_area: str
    cadre: Literal["teacher", "district_official", "central_official"]
    female: int = 0
    male: int = 0


class ActivityIn(BaseModel):
    """One activity from the Section C/D/E repeater."""
    focus_areas: list[str] = Field(default_factory=list)
    focus_area_other: str | None = None
    objectives: list[str] = Field(default_factory=list)
    tactics: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    activity_type: str | None = None
    intervention_levels: list[str] = Field(default_factory=list)
    activity_title: str | None = Field(None, max_length=300)
    description: str | None = None
    planned_vs_actual: str | None = None
    implementation_status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    indicators: list[OutputIndicatorIn] = Field(default_factory=list)
    training: list[TrainingRowIn] = Field(default_factory=list)


# ── Response schema ───────────────────────────────────────────────────────────

class SubmissionReportIn(BaseModel):
    """Consolidated submission-level payload from the Reporting Form.

    The active reporting period and the org's project are resolved server-side,
    so the client sends the narrative/quantitative submission fields plus the
    activities (with nested per-district indicators and training rows).
    """
    # Optional — admin may submit on behalf of an org; partners use their own.
    org_id: UUID | None = None

    # Optional — partner can provide a project title; if omitted the existing
    # project for the org is used (or a default one is created).
    project_title: str | None = None

    # Section B — geographic coverage entered by the partner
    districts: list[str] = Field(default_factory=list)
    chiefdoms: list[str] = Field(default_factory=list)

    # Sections C–E — activities with nested per-district indicators + training
    activities: list[ActivityIn] = Field(default_factory=list)

    # Section F — results narrative
    key_results: str | None = None
    observed_changes: str | None = None
    early_outcomes: str | None = None

    # Section G — finance
    expenditure: float | None = None
    expenditure_currency: str = "USD"
    budget_util: str | None = None

    # Section H — coordination
    gov_engaged: bool | None = None
    gov_engaged_list: str | None = None
    coordination_meetings: int = 0
    key_partners: str | None = None

    # Section I — challenges
    challenges: str | None = None
    risks: str | None = None
    mitigations: str | None = None

    # Section J — safeguarding
    safeguarding_cases: bool = False
    cases_reported: int = 0
    cases_referred: int = 0
    referral_pathway: str | None = None
    safeguarding_action: str | None = None

    # Section K — looking ahead
    planned_activities: str | None = None
    support_needed: str | None = None


class SubmissionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    org_id: UUID
    project_id: UUID
    reporting_period_id: UUID
    status: str
    submitted_at: datetime | None = None
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Aggregated from the submission's activities
    focus_areas: list[str] = Field(default_factory=list)
    # Enriched in the list endpoint via relationships
    org_name: str | None = None
    period_label: str | None = None


class ActivitySummary(BaseModel):
    """One activity within a submission, with rolled-up output indicators
    plus the per-district indicator rows and per-focus-area training detail."""
    model_config = {"from_attributes": True}
    activity_title: str | None = None
    activity_type: str | None = None
    implementation_status: str | None = None
    focus_areas: list[str] = Field(default_factory=list)
    focus_area_other: str | None = None
    objectives: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    students_f: int = 0
    students_m: int = 0
    teachers_f: int = 0
    teachers_m: int = 0
    community_f: int = 0
    community_m: int = 0
    schools_total: int = 0
    # Full breakdown for the verification view
    indicators: list[dict] = Field(default_factory=list)   # one dict per district
    training: list[dict] = Field(default_factory=list)      # district × focus area × cadre


class LocationSummary(BaseModel):
    model_config = {"from_attributes": True}
    district_name: str | None = None
    chiefdom_name: str | None = None
    community_name: str | None = None
    school_name: str | None = None


class UploadedFileOut(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    file_kind: str
    original_filename: str
    file_size_bytes: int
    mime_type: str | None = None
    storage_url: str | None = None
    created_at: datetime


class SubmissionDetail(SubmissionOut):
    """Full verification view — every field an admin needs to review a report."""
    # Section F — results narrative
    key_results: str | None = None
    observed_changes: str | None = None
    early_outcomes: str | None = None
    # Section G — finance
    expenditure: float | None = None
    budget_util: str | None = None
    # Section H — coordination
    gov_engaged: bool | None = None
    gov_engaged_list: str | None = None
    coordination_meetings: int = 0
    key_partners: str | None = None
    # Section I — challenges
    challenges: str | None = None
    risks: str | None = None
    mitigations: str | None = None
    # Section J — safeguarding
    safeguarding_cases: bool = False
    cases_reported: int = 0
    cases_referred: int = 0
    referral_pathway: str | None = None
    safeguarding_action: str | None = None
    # Section K — looking ahead
    planned_activities: str | None = None
    support_needed: str | None = None
    # Review metadata
    review_flag: str | None = None
    review_notes: str | None = None
    # Nested detail (built server-side)
    activities: list[ActivitySummary] = Field(default_factory=list)
    locations: list[LocationSummary] = Field(default_factory=list)
    files: list[UploadedFileOut] = Field(default_factory=list)

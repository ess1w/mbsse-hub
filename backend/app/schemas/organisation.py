"""
Pydantic schemas for Organisation and Project — field names match data dictionary Sections 5.1-5.2.
"""
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ProjectBrief(BaseModel):
    project_id: str
    project_title: str
    project_start: date | None = None
    project_end: date | None = None
    project_status: str = "Active"
    objective: list[str] = []
    focus_area: list[str] = []
    budget_usd: float | None = None
    budget_currency: str = "USD"
    funding_source: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrganisationOut(BaseModel):
    # Section 5.1 canonical fields
    org_id: str
    org_name: str
    org_type: str
    focal_person: str | None = None
    email: str | None = None
    phone: str | None = None
    sla_signed: bool = False
    status: str = "Pending"               # Active / Inactive / Pending

    # Extra admin fields
    districts: list[str] = []

    # Computed / enriched fields
    submission_status: str = "Not submitted"
    last_submitted: datetime | None = None
    project_count: int = 0
    objectives: list[str] = []
    focus_areas: list[str] = []
    projects: list[ProjectBrief] = []

    model_config = ConfigDict(from_attributes=True)


class OrganisationCreate(BaseModel):
    org_name: str
    org_type: str
    focal_person: str | None = None
    email: str | None = None
    phone: str | None = None
    sla_signed: bool = False
    status: str = "Pending"
    districts: list[str] = []
    notes: str | None = None

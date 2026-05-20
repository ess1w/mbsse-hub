"""
GET  /api/v1/organisations          → list (role-filtered)
GET  /api/v1/organisations/{id}     → detail

Field names match data dictionary Sections 5.1-5.2.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_any
from app.db.session import get_db
from app.models.organisation import Organisation
from app.models.project import Project
from app.models.reporting_period import ReportingPeriod
from app.models.submission import Submission
from app.models.user import User
from app.schemas.organisation import OrganisationOut, ProjectBrief

router = APIRouter(prefix="/organisations", tags=["organisations"])

# Human-readable labels for controlled vocabulary codes
OBJ_LABEL = {
    "obj1": "Promote Gender Equitable Behaviours",
    "obj2": "Strengthen Institutional Capacity",
    "obj3": "Ensure Sustained Policy Commitment",
}
FA_LABEL = {
    "fa1": "Prevention and Response to SRGBV",
    "fa2": "MHPSS",
    "fa3": "School Governance & Protection",
    "fa4": "Life Skills, Peacebuilding & SRH",
    "fa5": "WASH and School Environment",
    "fa6": "Social Norms and Participation",
    "fa7": "Social Protection",
    "fa8": "Other",
}


async def _build_response(orgs: list[Organisation], db: AsyncSession) -> list[OrganisationOut]:
    """Enrich orgs with project data and submission status."""
    if not orgs:
        return []

    org_ids = [o.org_id for o in orgs]

    # ── Projects ────────────────────────────────────────────────────────────
    proj_rows = (await db.execute(
        select(Project).where(Project.org_id.in_(org_ids))
    )).scalars().all()

    # ── Active reporting period + submission status ───────────────────────
    active_period = await db.scalar(
        select(ReportingPeriod).where(ReportingPeriod.is_active == True)
    )
    sub_map: dict[UUID, Submission] = {}
    if active_period:
        sub_rows = (await db.execute(
            select(Submission)
            .where(Submission.reporting_period_id == active_period.id)
            .where(Submission.org_id.in_(org_ids))
            .order_by(Submission.submitted_at.desc())
        )).scalars().all()
        for sub in sub_rows:
            if sub.org_id not in sub_map:
                sub_map[sub.org_id] = sub

    # ── Group projects by org ─────────────────────────────────────────────
    projects_by_org: dict[UUID, list[Project]] = {}
    for p in proj_rows:
        projects_by_org.setdefault(p.org_id, []).append(p)

    result = []
    for org in orgs:
        org_projects = projects_by_org.get(org.org_id, [])

        # Aggregate objectives and focus areas across all projects
        objectives = sorted(set(
            OBJ_LABEL.get(obj, obj)
            for p in org_projects
            for obj in (p.objective or [])
        ))
        focus_areas = sorted(set(
            FA_LABEL.get(fa, fa)
            for p in org_projects
            for fa in (p.focus_area or [])
        ))

        sub = sub_map.get(org.org_id)
        sub_status = (sub.status.title() if sub else "Not submitted")

        # Build project briefs
        project_briefs = [
            ProjectBrief(
                project_id=str(p.project_id),
                project_title=p.project_title,
                project_start=p.project_start,
                project_end=p.project_end,
                project_status=p.project_status or "Active",
                objective=[OBJ_LABEL.get(o, o) for o in (p.objective or [])],
                focus_area=[FA_LABEL.get(fa, fa) for fa in (p.focus_area or [])],
                budget_usd=float(p.budget_usd) if p.budget_usd else None,
                budget_currency=p.budget_currency or "USD",
                funding_source=p.funding_source,
            )
            for p in org_projects
        ]

        result.append(OrganisationOut(
            org_id=str(org.org_id),
            org_name=org.org_name,
            org_type=org.org_type,
            focal_person=org.focal_person,
            email=org.email,
            phone=org.phone,
            sla_signed=org.sla_signed,
            status=org.status,
            districts=sorted(org.districts or []),
            submission_status=sub_status,
            last_submitted=sub.submitted_at if sub else None,
            project_count=len(org_projects),
            objectives=objectives,
            focus_areas=focus_areas,
            projects=project_briefs,
        ))

    return result


@router.get("/", response_model=list[OrganisationOut])
async def list_organisations(
    search: str | None = Query(None),
    org_type: str | None = Query(None),
    sla_signed: bool | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any),
):
    q = select(Organisation).where(Organisation.status != "Inactive")

    if current_user.role == "partner":
        q = q.where(Organisation.org_id == current_user.organisation_id)
    if search:
        q = q.where(Organisation.org_name.ilike(f"%{search}%"))
    if org_type:
        q = q.where(Organisation.org_type == org_type)
    if sla_signed is not None:
        q = q.where(Organisation.sla_signed == sla_signed)
    if status:
        q = q.where(Organisation.status == status)

    orgs = (await db.execute(q.order_by(Organisation.org_name))).scalars().all()
    return await _build_response(list(orgs), db)


@router.get("/{org_id}", response_model=OrganisationOut)
async def get_organisation(
    org_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_any),
):
    org = await db.get(Organisation, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    if current_user.role == "partner" and org.org_id != current_user.organisation_id:
        raise HTTPException(status_code=403, detail="Access denied")

    built = await _build_response([org], db)
    return built[0]

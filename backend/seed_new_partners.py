"""
Add partner organisations that were missing from the original registry.

Source: partner-supplied mapping-tool spreadsheets (same format as
'Mapping tool 2025 for SRGBV coordination hub FINAL.xlsx'):
  - SEND SL-Mapping tool ...                 → SEND SIERRA LEONE (2 projects)
  - Mapping tool ... _FOCUS 1000.xlsx        → FOCUS 1000 (1 project)

Inserts organisations + projects only (no activities/reports — partners file
those through the Reporting Form). Idempotent and authoritative for these two
partners: if the organisation already exists (e.g. SEND was in the original
registry with stale data) it is updated and its projects are reconciled to the
spreadsheet. Demo submissions (attributed to an admin) for these partners are
cleared so their status reflects reality; real partner-filed reports are kept.

Run from backend/:
    python seed_new_partners.py
"""
import asyncio
import os
import uuid
from datetime import date
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub",
).replace("postgresql+asyncpg://", "postgresql://")


def _dt(s):
    return date.fromisoformat(s) if s else None


# Focus area for both partners is "Prevention and Response to SRGBV" → fa1.
PARTNERS = [
    {
        "org_name": "SEND SIERRA LEONE",
        "org_type": "CSO",
        "focal_person": "Hassanatu Bah",
        "email": "hassanatu@sendsierraleone.com",
        "phone": "078-464-455",
        "districts": ["Kailahun", "Moyamba"],
        "objectives": [],
        "projects": [
            {
                "title": "SPOTLIGHT INITIATIVE PROGRAMME",
                "start": "2026-03-06", "end": "2026-12-30",
                "focus_area": ["fa1"],
                "districts": ["Kailahun", "Moyamba"],
                "activity_summary": (
                    "The spotlight initiative activities are designed to strengthen communities in "
                    "addressing Gender Based Violence through strengthening 3 existing CLCs in target "
                    "districts, to offer out-of-school CSE and life skills such as communication, "
                    "negotiation, assertiveness, refusal and livelihood skills that will empower girls "
                    "to prevent GBV/HP and improve access to SRHR. Male engagement programme focused on "
                    "promoting positive masculinity, transform men and boys into community advocates to "
                    "address GBV and serve as role models on issues around harmful practices."
                ),
                "funding_source": "UNFPA",
                "budget_usd": 291741.24, "budget_currency": "USD",
                "gov_counterpart": ["MBSSE", "MoGCA", "MoSW"],
                "key_partners": "FINE SL, Happy Kids and Adolescent, Restless Development.",
                "status": "Active",
            },
            {
                # NOTE: source title cell was truncated ("SPOTLIGHT INITIATIVE IN SIERRA ");
                # completed to the evident title — adjust in the admin Edit screen if needed.
                "title": "SPOTLIGHT INITIATIVE IN SIERRA LEONE",
                # NOTE: source end date was "0ctober, 2027" (no day) — set to 1 Oct 2027.
                "start": "2026-03-16", "end": "2027-10-01",
                "focus_area": ["fa1"],
                "districts": ["Kailahun"],
                "activity_summary": (
                    "The UNICEF-Spotlight project employs a holistic, multi-sectoral, and transformative "
                    "prevention approach aligned with the Spotlight Initiative model. It integrates "
                    "school-based programming, community mobilization, systems strengthening, SBCC, and "
                    "youth-led advocacy to address the structural drivers of VAWG. The approach actively "
                    "engages women, men, boys, girls, traditional leaders, parents, service providers, "
                    "and institutions, ensuring collective action toward sustainable social change and "
                    "the realization of gender justice in Kailahun District."
                ),
                "funding_source": "UNICEF",
                "budget_usd": 211490.96, "budget_currency": "USD",
                "gov_counterpart": ["MBSSE", "TSC", "MoGCA", "MoSW", "Local Council"],
                "key_partners": "Plan International Sierra Leone and Focus 1000",
                "status": "Active",
            },
        ],
    },
    {
        "org_name": "FOCUS 1000",
        "org_type": "CSO",
        "focal_person": "Mariama Awuko",
        "email": "awukumariama@gmail.com",
        "phone": "079035854",
        "districts": ["Falaba"],
        "objectives": [],
        "projects": [
            {
                "title": "Spotlight Initiative",
                "start": "2026-01-01", "end": "2027-06-30",
                "focus_area": ["fa1"],
                "districts": ["Falaba"],
                "activity_summary": (
                    "Safe spaces for students - School clubs and peer-support groups - Training of "
                    "teachers, mentors, SQAMs, and community structures - Reporting and referral "
                    "mechanisms - Service provision for survivors - Other context-specific "
                    "interventions (to be specified)."
                ),
                "funding_source": "European Union",
                # Source budget was "NLE 00000000" (placeholder) — left unset.
                "budget_usd": None, "budget_currency": "NLE",
                "gov_counterpart": ["Ministry of Gender and Children's Affairs", "MBSSE"],
                "key_partners": "UNICEF, Plan SL, SEND SL",
                "status": "Active",
            },
        ],
    },
]


async def _upsert_project(conn, org_id, p, proj):
    """Insert a project, or update it in place if one with the same title exists
    (update-in-place keeps any submission foreign keys valid)."""
    pid = await conn.fetchval(
        "SELECT project_id FROM projects WHERE org_id = $1 AND project_title = $2",
        org_id, proj["title"],
    )
    cols = (
        _dt(proj.get("start")), _dt(proj.get("end")),
        p.get("objectives", []), [], proj.get("focus_area", []),
        proj.get("activity_summary"), proj.get("funding_source"),
        proj.get("budget_usd"), proj.get("budget_currency", "USD"),
        proj.get("gov_counterpart", []), proj.get("key_partners"),
        proj.get("status", "Active"),
    )
    if pid:
        await conn.execute(
            """UPDATE projects SET
                   project_start=$2, project_end=$3, objective=$4, tactic=$5,
                   focus_area=$6, activity_summary=$7, funding_source=$8,
                   budget_usd=$9, budget_currency=$10, gov_counterpart=$11,
                   key_partners=$12, project_status=$13
               WHERE project_id=$1""",
            pid, *cols,
        )
    else:
        await conn.execute(
            """INSERT INTO projects
                  (project_id, org_id, project_title, project_start, project_end,
                   objective, tactic, focus_area,
                   activity_summary, funding_source, budget_usd, budget_currency,
                   gov_counterpart, key_partners, project_status)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)""",
            str(uuid.uuid4()), org_id, proj["title"], *cols,
        )


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database\n")

    created = updated = 0
    for p in PARTNERS:
        org_id = await conn.fetchval(
            "SELECT org_id FROM organisations WHERE org_name = $1", p["org_name"]
        )
        if org_id:
            # Org already in the registry (possibly with stale data) — correct it.
            await conn.execute(
                """UPDATE organisations SET
                       org_type=$2, focal_person=$3, email=$4, phone=$5, districts=$6
                   WHERE org_id=$1""",
                org_id, p["org_type"], p.get("focal_person"),
                p.get("email"), p.get("phone"), p.get("districts", []),
            )
            updated += 1
            tag = "updated"
        else:
            org_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO organisations
                      (org_id, org_name, org_type, focal_person, email, phone,
                       sla_signed, status, districts)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
                org_id, p["org_name"], p["org_type"],
                p.get("focal_person"), p.get("email"), p.get("phone"),
                False, "Active", p.get("districts", []),
            )
            created += 1
            tag = "created"

        # Clear demo submissions (seed data is attributed to an admin user) so
        # these real partners show their true status. Real partner-filed reports
        # (submitted_by a partner user) are preserved across re-runs.
        await conn.execute(
            """DELETE FROM submissions
               WHERE org_id = $1
                 AND submitted_by IN (SELECT id FROM users WHERE role = 'admin')""",
            org_id,
        )

        # Reconcile projects to the spreadsheet
        wanted = [proj["title"] for proj in p["projects"]]
        for proj in p["projects"]:
            await _upsert_project(conn, org_id, p, proj)

        # Remove stale projects not in the spreadsheet, but only if nothing
        # references them (no submissions) — never orphan real data.
        stale = await conn.fetch(
            "SELECT project_id, project_title FROM projects "
            "WHERE org_id = $1 AND project_title <> ALL($2::text[])",
            org_id, wanted,
        )
        for row in stale:
            has_sub = await conn.fetchval(
                "SELECT 1 FROM submissions WHERE project_id = $1 LIMIT 1",
                row["project_id"],
            )
            if not has_sub:
                await conn.execute(
                    "DELETE FROM projects WHERE project_id = $1", row["project_id"]
                )
                print(f"     – removed stale project: {row['project_title']!r}")

        n = len(p["projects"])
        print(f"  ✓  {p['org_name']} {tag} ({n} project{'s' if n != 1 else ''})")

    await conn.close()
    print(f"\nDone — {created} created, {updated} updated.")


if __name__ == "__main__":
    asyncio.run(main())

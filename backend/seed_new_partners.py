"""
Add partner organisations that were missing from the original registry.

Source: partner-supplied mapping-tool spreadsheets (same format as
'Mapping tool 2025 for SRGBV coordination hub FINAL.xlsx'):
  - SEND SL-Mapping tool ...                 → SEND SIERRA LEONE (2 projects)
  - Mapping tool ... _FOCUS 1000.xlsx        → FOCUS 1000 (1 project)

Mirrors seed_organisations.py: inserts organisations + projects only (no
activities/reports — partners file those through the Reporting Form). Idempotent
— skips an organisation that already exists by name.

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


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database\n")

    inserted = skipped = 0
    for p in PARTNERS:
        existing = await conn.fetchval(
            "SELECT org_id FROM organisations WHERE org_name = $1", p["org_name"]
        )
        if existing:
            print(f"  skip  {p['org_name']} (already exists)")
            skipped += 1
            continue

        org_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO organisations
              (org_id, org_name, org_type, focal_person, email, phone,
               sla_signed, status, districts)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            org_id, p["org_name"], p["org_type"],
            p.get("focal_person"), p.get("email"), p.get("phone"),
            False,                       # sla_signed — partners upload/await approval
            "Active",
            p.get("districts", []),
        )

        for proj in p["projects"]:
            await conn.execute(
                """
                INSERT INTO projects
                  (project_id, org_id, project_title, project_start, project_end,
                   objective, tactic, focus_area,
                   activity_summary, funding_source, budget_usd, budget_currency,
                   gov_counterpart, key_partners, project_status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                """,
                str(uuid.uuid4()), org_id,
                proj["title"], _dt(proj.get("start")), _dt(proj.get("end")),
                p.get("objectives", []), [], proj.get("focus_area", []),
                proj.get("activity_summary"), proj.get("funding_source"),
                proj.get("budget_usd"), proj.get("budget_currency", "USD"),
                proj.get("gov_counterpart", []), proj.get("key_partners"),
                proj.get("status", "Active"),
            )

        n = len(p["projects"])
        print(f"  ✓  {p['org_name']} ({n} project{'s' if n != 1 else ''})")
        inserted += 1

    await conn.close()
    print(f"\nDone — {inserted} organisations inserted, {skipped} skipped.")


if __name__ == "__main__":
    asyncio.run(main())

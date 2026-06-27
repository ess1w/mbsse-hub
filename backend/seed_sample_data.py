"""
Seeds realistic submission data for the Jan–Feb 2026 AND Mar–Apr 2026
reporting periods, so that Superset analytics charts have data regardless
of which period is currently active.

Run from backend/ directory:
    python seed_sample_data.py

Safe to re-run — skips orgs that already have a submission for a period.
To remove this data before going live, run: python cleanup_seed_data.py
"""
import asyncio, os, uuid, random
from datetime import datetime, timezone, date
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

# Seed data for both the historical period AND the currently active one
PERIODS = [
    {
        "label":      "Jan–Feb 2026",
        "start_date": date(2026, 1, 1),
        "end_date":   date(2026, 2, 28),
        "deadline":   date(2026, 3, 15),
        "is_active":  False,
        # Dates used for submitted_at / verified_at
        "sub_months": (1, 2),
        "ver_month":  2,
    },
    {
        "label":      "Mar–Apr 2026",
        "start_date": date(2026, 3, 1),
        "end_date":   date(2026, 4, 30),
        "deadline":   date(2026, 5, 15),
        "is_active":  True,
        "sub_months": (3, 4),
        "ver_month":  4,
    },
]

FOCUS_AREAS    = ["SRGBV Prevention & Response", "MHPSS", "School Governance",
                  "Life Skills / SRH", "WASH", "Social Norms", "Social Protection"]
OBJECTIVES     = ["obj1", "obj2", "obj3"]
ACTIVITY_TYPES = ["Training / Capacity Building", "Community Outreach",
                  "Awareness Campaign", "Safe Space Activities", "Policy / Advocacy"]
DISTRICTS      = ["Bo", "Bombali", "Bonthe", "Falaba", "Kailahun", "Kambia",
                  "Karene", "Kenema", "Koinadugu", "Kono", "Moyamba",
                  "Port Loko", "Pujehun", "Tonkolili",
                  "Western Area Rural", "Western Area Urban"]
IMPL_STATUSES  = ["Completed", "Ongoing", "Delayed"]


def rnd(lo, hi): return random.randint(lo, hi)


async def seed_period(conn, period_cfg, admin_id):
    label = period_cfg["label"]

    # ── Fetch or create the period ────────────────────────────────────────────
    period = await conn.fetchrow(
        "SELECT id, label FROM reporting_periods WHERE label = $1", label
    )
    if not period:
        pid = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO reporting_periods (id, label, start_date, end_date, deadline, is_active)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            pid, label,
            period_cfg["start_date"], period_cfg["end_date"],
            period_cfg["deadline"], period_cfg["is_active"],
        )
        period_id = pid
        print(f"  Created reporting period: {label}")
    else:
        period_id = str(period["id"])
        print(f"  Found existing period: {label} ({period_id})")

    # ── Fetch orgs without a submission for this period ───────────────────────
    all_orgs = await conn.fetch(
        """SELECT org_id, org_name FROM organisations
           WHERE org_id NOT IN (
               SELECT org_id FROM submissions WHERE reporting_period_id = $1
           )
           ORDER BY org_name""",
        period_id,
    )

    if not all_orgs:
        print(f"  ✓ All organisations already have a submission for {label}.")
        return 0

    print(f"  Orgs without a {label} submission: {len(all_orgs)}")
    random.shuffle(all_orgs := list(all_orgs))

    # Target: 38 submitted (22 verified + 16 pending), 10 draft, rest = no submission
    n_verified  = min(22, len(all_orgs))
    n_submitted = min(38, len(all_orgs)) - n_verified
    n_draft     = min(10, max(0, len(all_orgs) - n_verified - n_submitted))

    assignments = (
        [("verified",  True)]  * n_verified  +
        [("submitted", False)] * n_submitted +
        [("draft",     False)] * n_draft
    )
    orgs_to_seed = all_orgs[:len(assignments)]
    sub_months   = period_cfg["sub_months"]
    ver_month    = period_cfg["ver_month"]

    created = 0
    for org, (status, do_verify) in zip(orgs_to_seed, assignments):
        org_id = str(org["org_id"])
        sub_id = str(uuid.uuid4())
        act_id = str(uuid.uuid4())

        submitted_at = (
            datetime(2026, random.choice(sub_months), random.randint(5, 25),
                     random.randint(8, 17), tzinfo=timezone.utc)
            if status in ("submitted", "verified") else None
        )
        verified_at = (
            datetime(2026, ver_month, random.randint(10, 28),
                     random.randint(8, 17), tzinfo=timezone.utc)
            if do_verify else None
        )

        focus     = random.sample(FOCUS_AREAS, random.randint(1, 3))
        objective = random.choice(OBJECTIVES)

        # Resolve or create a project
        proj_id = await conn.fetchval(
            "SELECT project_id FROM projects WHERE org_id = $1 LIMIT 1", org_id
        )
        if not proj_id:
            proj_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO projects (project_id, org_id, project_title, project_status)
                   VALUES ($1, $2, $3, 'Active') ON CONFLICT DO NOTHING""",
                proj_id, org_id, f"SRGBV Programme — {org['org_name']}",
            )

        await conn.execute(
            """INSERT INTO submissions (
                   id, org_id, project_id, reporting_period_id,
                   submitted_by, verified_by, status,
                   key_results, observed_changes, early_outcomes,
                   expenditure, expenditure_currency, budget_util,
                   gov_engaged, coordination_meetings,
                   challenges, planned_activities,
                   safeguarding_cases, cases_reported, cases_referred,
                   submitted_at, verified_at
               ) VALUES (
                   $1, $2, $3, $4,
                   $5, $6, $7,
                   $8, $9, $10,
                   $11, 'USD', $12,
                   $13, $14,
                   $15, $16,
                   $17, $18, $19,
                   $20, $21
               )""",
            sub_id, org_id, proj_id, period_id,
            str(admin_id), str(admin_id) if do_verify else None,
            status,
            f"Reached {rnd(200, 5000)} beneficiaries across {rnd(2, 8)} schools.",
            "Observed improvements in awareness of SRGBV reporting mechanisms.",
            "Early signs of increased referrals to support services.",
            float(rnd(10000, 150000)),
            random.choice(["On track", "Under-spending", "Over-spending"]),
            random.choice([True, False]), rnd(1, 6),
            "Access constraints in remote communities." if rnd(0, 1) else None,
            "Continue school-based sessions next period.",
            rnd(0, 1) == 1, rnd(0, 5), rnd(0, 3),
            submitted_at, verified_at,
        )

        act_district = random.choice(DISTRICTS)
        await conn.execute(
            """INSERT INTO activities (
                   activity_id, submission_id,
                   focus_areas, objectives, activity_type,
                   activity_title, description, implementation_status,
                   start_date, end_date, districts
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)""",
            act_id, sub_id,
            focus, [objective], random.choice(ACTIVITY_TYPES),
            f"SRGBV Awareness and Prevention — {act_district}",
            "Conducted school-based sessions on SRGBV prevention and referral pathways.",
            random.choice(IMPL_STATUSES),
            date(2026, sub_months[0], rnd(5, 20)),
            date(2026, sub_months[-1], rnd(1, 25)),
            [act_district],
        )

        await conn.execute(
            """INSERT INTO submission_locations (location_id, submission_id, district_name)
               VALUES ($1, $2, $3)""",
            str(uuid.uuid4()), sub_id, act_district,
        )

        f_stud = rnd(100, 3000)
        m_stud = rnd(80, 2000)
        f_tchr = rnd(5, 40)
        m_tchr = rnd(3, 30)
        await conn.execute(
            """INSERT INTO output_indicators (
                   activity_id, district_name,
                   schools_primary, schools_jss, schools_sss,
                   students_inschool_f, students_inschool_m,
                   students_inschool_age_10_14, students_inschool_age_15_19,
                   teachers_f, teachers_m,
                   community_sessions, community_members_f, community_members_m
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
            act_id, act_district,
            rnd(1, 5), rnd(1, 4), rnd(0, 3),
            f_stud, m_stud,
            rnd(50, f_stud), rnd(30, m_stud),
            f_tchr, m_tchr,
            rnd(0, 4), rnd(0, 200), rnd(0, 150),
        )
        created += 1

    print(f"  ✓ Created {created} submissions ({n_verified} verified · {n_submitted} submitted · {n_draft} draft)")
    return created


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    admin_id = await conn.fetchval("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    if not admin_id:
        print("✗ No admin user found. Run seed_admin.py first.")
        await conn.close()
        return

    total = 0
    for period_cfg in PERIODS:
        print(f"\n── {period_cfg['label']} ─────────────────────────────────")
        total += await seed_period(conn, period_cfg, admin_id)

    await conn.close()
    print(f"\n✓ Done — {total} submissions created across {len(PERIODS)} periods.")
    print("To remove this data before going live: python cleanup_seed_data.py")


if __name__ == "__main__":
    asyncio.run(main())

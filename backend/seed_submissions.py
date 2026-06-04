"""
Seeds realistic submission data for the active reporting period.

Creates:
  - 38 submitted (22 verified, 16 pending review)
  - 10 draft
  - 5 with no submission (remaining orgs)
  - 1 activity + output_indicators row per submission

Run from backend/ directory:
    python seed_submissions.py

Safe to re-run — skips orgs that already have a submission for the period.
"""
import asyncio, os, uuid, random
from datetime import datetime, timezone, date, timedelta
import asyncpg
from passlib.context import CryptContext

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

FOCUS_AREAS   = ["SRGBV Prevention & Response", "MHPSS", "School Governance",
                 "Life Skills / SRH", "WASH", "Social Norms", "Social Protection"]
OBJECTIVES    = ["obj1", "obj2", "obj3"]
ACTIVITY_TYPES = ["Training / Capacity Building", "Community Outreach",
                  "Awareness Campaign", "Safe Space Activities", "Policy / Advocacy"]
DISTRICTS     = ["Bo", "Bombali", "Bonthe", "Falaba", "Kailahun", "Kambia",
                 "Karene", "Kenema", "Koinadugu", "Kono", "Moyamba",
                 "Port Loko", "Pujehun", "Tonkolili",
                 "Western Area Rural", "Western Area Urban"]
IMPL_STATUSES = ["Completed", "Ongoing", "Delayed"]


def rnd(lo, hi): return random.randint(lo, hi)


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    # ── Fetch active period ───────────────────────────────────────────────────
    period = await conn.fetchrow(
        "SELECT id, label FROM reporting_periods WHERE is_active = true LIMIT 1"
    )
    if not period:
        print("✗ No active reporting period found. Run seed_organisations.py first.")
        await conn.close()
        return
    period_id = str(period["id"])
    print(f"Period: {period['label']} ({period_id})")

    # ── Fetch admin user id ───────────────────────────────────────────────────
    admin_id = await conn.fetchval("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    if not admin_id:
        print("✗ No admin user found. Run seed_admin.py first.")
        await conn.close()
        return

    # ── Fetch orgs that don't yet have a submission ───────────────────────────
    all_orgs = await conn.fetch(
        """SELECT org_id, org_name FROM organisations
           WHERE org_id NOT IN (
               SELECT org_id FROM submissions WHERE reporting_period_id = $1
           )
           ORDER BY org_name""",
        period_id,
    )

    if not all_orgs:
        print("✓ All organisations already have a submission for this period.")
        await conn.close()
        return

    print(f"Orgs without a submission: {len(all_orgs)}")
    random.shuffle(all_orgs := list(all_orgs))

    # ── Assign statuses ───────────────────────────────────────────────────────
    # Target: 38 submitted (22 verified + 16 pending), 10 draft, rest = no submission
    n_verified = min(22, len(all_orgs))
    n_submitted = min(38, len(all_orgs)) - n_verified
    n_draft     = min(10, max(0, len(all_orgs) - n_verified - n_submitted))

    assignments = (
        [("verified",  True)]  * n_verified  +
        [("submitted", False)] * n_submitted +
        [("draft",     False)] * n_draft
    )
    # Any remaining orgs get no submission at all
    orgs_to_seed = all_orgs[:len(assignments)]

    created = 0
    for org, (status, do_verify) in zip(orgs_to_seed, assignments):
        org_id   = str(org["org_id"])
        sub_id   = str(uuid.uuid4())
        act_id   = str(uuid.uuid4())

        submitted_at = (
            datetime(2026, random.randint(1,2), random.randint(5,25),
                     random.randint(8,17), tzinfo=timezone.utc)
            if status in ("submitted", "verified") else None
        )
        verified_at = (
            datetime(2026, 2, random.randint(10,28),
                     random.randint(8,17), tzinfo=timezone.utc)
            if do_verify else None
        )

        focus = random.sample(FOCUS_AREAS, random.randint(1, 3))
        objective = random.choice(OBJECTIVES)

        # Create a project for this org (required FK)
        proj_id = await conn.fetchval(
            "SELECT project_id FROM projects WHERE org_id = $1 LIMIT 1",
            org_id,
        )
        if not proj_id:
            proj_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO projects
                       (project_id, org_id, project_title, project_status)
                   VALUES ($1, $2, $3, 'Active')
                   ON CONFLICT DO NOTHING""",
                proj_id, org_id,
                f"SRGBV Programme — {org['org_name']}",
            )

        # ── Submission row ────────────────────────────────────────────────────
        await conn.execute(
            """INSERT INTO submissions (
                   id, org_id, project_id, reporting_period_id,
                   submitted_by, verified_by,
                   status,
                   key_results, observed_changes, early_outcomes,
                   expenditure, expenditure_currency, budget_util,
                   gov_engaged, coordination_meetings,
                   challenges, planned_activities,
                   safeguarding_cases, cases_reported, cases_referred,
                   submitted_at, verified_at
               ) VALUES (
                   $1, $2, $3, $4,
                   $5, $6,
                   $7,
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
            f"Reached {rnd(200,5000)} beneficiaries across {rnd(2,8)} schools.",
            "Observed improvements in awareness of SRGBV reporting mechanisms.",
            "Early signs of increased referrals to support services.",
            float(rnd(10000, 150000)),
            random.choice(["On track", "Under-spending", "Over-spending"]),
            random.choice([True, False]), rnd(1, 6),
            "Access constraints in remote communities." if rnd(0,1) else None,
            "Continue school-based sessions next period.",
            rnd(0, 1) == 1, rnd(0, 5), rnd(0, 3),
            submitted_at, verified_at,
        )

        # ── Activity row ──────────────────────────────────────────────────────
        await conn.execute(
            """INSERT INTO activities (
                   activity_id, submission_id,
                   focus_areas, objectives, activity_type,
                   activity_title, description,
                   implementation_status,
                   start_date, end_date
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)""",
            act_id, sub_id,
            focus, [objective], random.choice(ACTIVITY_TYPES),
            f"SRGBV Awareness and Prevention — {random.choice(DISTRICTS)}",
            "Conducted school-based sessions on SRGBV prevention and referral pathways.",
            random.choice(IMPL_STATUSES),
            date(2026, 1, rnd(5, 20)), date(2026, 2, rnd(1, 25)),
        )

        # ── Output indicators row ─────────────────────────────────────────────
        f_stud = rnd(100, 3000)
        m_stud = rnd(80, 2000)
        f_tchr = rnd(5, 40)
        m_tchr = rnd(3, 30)
        await conn.execute(
            """INSERT INTO output_indicators (
                   activity_id,
                   schools_primary, schools_jss, schools_sss,
                   students_inschool_f, students_inschool_m,
                   students_inschool_age_10_14, students_inschool_age_15_19,
                   teachers_f, teachers_m,
                   community_sessions, community_members_f, community_members_m
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
            act_id,
            rnd(1,5), rnd(1,4), rnd(0,3),
            f_stud, m_stud,
            rnd(50, f_stud), rnd(30, m_stud),
            f_tchr, m_tchr,
            rnd(0, 4), rnd(0, 200), rnd(0, 150),
        )

        created += 1

    await conn.close()
    print(f"\n✓ Created {created} submissions")
    print(f"  {n_verified} verified · {n_submitted} submitted · {n_draft} draft")
    print(f"  {len(all_orgs) - len(orgs_to_seed)} orgs left with no submission")


if __name__ == "__main__":
    asyncio.run(main())

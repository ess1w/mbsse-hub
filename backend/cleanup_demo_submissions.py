"""
Remove demo/sample submissions from a live database.

The seed scripts created submissions attributed to an admin user (submitted_by =
an admin). Real partner reports are attributed to the partner's own user, so we
can safely delete the admin-attributed ones — this clears the fake "verified"
submissions that would otherwise block partners from submitting real data.

Runs only in production (ENVIRONMENT=production) unless FORCE_CLEANUP is set.
Idempotent and safe to run on every deploy.

Deleting a submission cascades to its activities, indicators, locations and files.
"""
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub",
).replace("postgresql+asyncpg://", "postgresql://")


async def main():
    if os.getenv("ENVIRONMENT", "").lower() != "production" and not os.getenv("FORCE_CLEANUP"):
        print("  ↷ Skipping demo-submission cleanup (not production).")
        return

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Demo submissions created by the seed scripts (attributed to an admin).
        r1 = await conn.execute(
            """
            DELETE FROM submissions
            WHERE submitted_by IN (SELECT id FROM users WHERE role = 'admin')
            """
        )
        # 2. Any submissions left in the retired seed-default periods (Jan–Feb /
        #    Mar–Apr 2026) while they are NOT the active period. These periods were
        #    never a real reporting cycle for the pilot, so anything there (incl.
        #    reports accidentally saved against them) is safe to remove. If an admin
        #    ever makes one of these active again, it is excluded automatically.
        r2 = await conn.execute(
            """
            DELETE FROM submissions
            WHERE reporting_period_id IN (
                SELECT id FROM reporting_periods
                WHERE is_active = false
                  AND start_date IN (DATE '2026-01-01', DATE '2026-03-01')
            )
            """
        )
        print(f"  ✓ Demo submissions cleanup: admin={r1}, retired-periods={r2}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

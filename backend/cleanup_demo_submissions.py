"""
Remove seed/demo submissions for the CURRENT active reporting period only.

The active-period demo submissions (created by seed_submissions.py, attributed to
an admin user) are the fake "verified" reports that can block partners from
submitting real data. Real partner reports are attributed to the partner's own
user, so they are preserved.

IMPORTANT: this only ever touches the currently-active period. Historical periods
(e.g. the Mar–Apr 2026 baseline) are never modified, regardless of attribution.

Runs only in production (ENVIRONMENT=production) unless FORCE_CLEANUP is set.
Idempotent and safe to run on every deploy.
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
        result = await conn.execute(
            """
            DELETE FROM submissions
            WHERE submitted_by IN (SELECT id FROM users WHERE role = 'admin')
              AND reporting_period_id = (
                  SELECT id FROM reporting_periods
                  WHERE is_active = true
                  ORDER BY start_date DESC
                  LIMIT 1
              )
            """
        )
        print(f"  ✓ Active-period demo submissions cleanup: {result}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

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
        result = await conn.execute(
            """
            DELETE FROM submissions
            WHERE submitted_by IN (SELECT id FROM users WHERE role = 'admin')
            """
        )
        # result looks like 'DELETE <n>'
        print(f"  ✓ Demo submissions cleanup: {result}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

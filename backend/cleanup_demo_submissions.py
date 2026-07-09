"""
Remove ALL demo/sample submissions — the pre-production wipe.

Demo submissions (created by the sample-data seeds) are attributed to an admin
user. Real partner reports are attributed to the partner's own user, so they are
always preserved.

This is a DELIBERATE step, not an automatic one. It only runs when the
RUN_DEMO_CLEANUP environment variable is set. Run it once just before going to
production:
    1. Remove SEED_DEMO_DATA from the environment (stop regenerating demo data).
    2. Set RUN_DEMO_CLEANUP=1 and deploy — this wipes the demo submissions.
    3. Remove RUN_DEMO_CLEANUP again.

During the prototype/pilot phase it stays dormant, so demo data is preserved.
"""
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub",
).replace("postgresql+asyncpg://", "postgresql://")


async def main():
    if not os.getenv("RUN_DEMO_CLEANUP"):
        print("  ↷ Skipping demo cleanup (set RUN_DEMO_CLEANUP=1 to wipe demo data before production).")
        return

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.execute(
            """
            DELETE FROM submissions
            WHERE submitted_by IN (SELECT id FROM users WHERE role = 'admin')
            """
        )
        print(f"  ✓ Demo submissions wiped (real partner reports preserved): {result}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

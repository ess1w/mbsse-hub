"""
Removes all sample / seed data before going into production.

What is removed:
  - All submissions (and their activities, output_indicators, locations,
    uploaded_files) for the Jan–Feb 2026 sample period
  - All submissions and uploaded_files for Mar–Apr 2026 (test submissions)
  - Pilot partner users created by seed_pilot_users.py
  - The demo partner / viewer users created by seed_users.py
  - Audit log entries for the removed users/submissions

What is NOT removed:
  - Organisations and projects (real partner registry data)
  - Reporting periods (configuration data)
  - Admin users
  - Districts

Run from backend/ directory:
    python cleanup_seed_data.py

You will be asked to confirm before any data is deleted.
"""
import asyncio
import os
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

SEED_USER_EMAILS = [
    # seed_pilot_users.py
    "s.kamara@plan-international.org",
    "i.koroma@savethechildren.org",
    "m.conteh@streetchildsl.org",
    "h.jalloh@worldvision.org",
    "v.momoh@actionaid.org",
    # seed_users.py defaults
    "partner@mbsse.gov.sl",
    "viewer@mbsse.gov.sl",
]

SAMPLE_PERIOD_LABELS = ["Jan–Feb 2026", "Mar–Apr 2026"]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    # ── Preview what will be deleted ─────────────────────────────────────────
    print("=" * 60)
    print("CLEANUP PREVIEW — nothing deleted yet")
    print("=" * 60)

    # Count submissions per sample period
    for label in SAMPLE_PERIOD_LABELS:
        period = await conn.fetchrow(
            "SELECT id FROM reporting_periods WHERE label = $1", label
        )
        if period:
            n = await conn.fetchval(
                "SELECT COUNT(*) FROM submissions WHERE reporting_period_id = $1",
                str(period["id"]),
            )
            print(f"  {n} submissions for period '{label}'")
        else:
            print(f"  Period '{label}' not found — nothing to delete")

    # Count seed users
    seed_users = await conn.fetch(
        "SELECT email, role FROM users WHERE email = ANY($1::text[])",
        SEED_USER_EMAILS,
    )
    print(f"  {len(seed_users)} seed/pilot users:")
    for u in seed_users:
        print(f"    [{u['role']:8s}] {u['email']}")

    print()
    confirm = input("Type 'DELETE' to proceed, or anything else to cancel: ").strip()
    if confirm != "DELETE":
        print("Cancelled — no data was deleted.")
        await conn.close()
        return

    print()
    total_subs = 0
    total_files = 0

    # ── Delete submissions for sample periods ────────────────────────────────
    for label in SAMPLE_PERIOD_LABELS:
        period = await conn.fetchrow(
            "SELECT id FROM reporting_periods WHERE label = $1", label
        )
        if not period:
            continue
        period_id = str(period["id"])

        sub_ids = [str(r["id"]) for r in await conn.fetch(
            "SELECT id FROM submissions WHERE reporting_period_id = $1", period_id
        )]
        if not sub_ids:
            continue

        # Cascade-delete children first (FK constraints without ON DELETE CASCADE)
        await conn.execute(
            "DELETE FROM uploaded_files WHERE submission_id = ANY($1::uuid[])", sub_ids
        )
        await conn.execute(
            "DELETE FROM submission_locations WHERE submission_id = ANY($1::uuid[])", sub_ids
        )
        # Delete output_indicators via activity IDs
        act_ids = [str(r["activity_id"]) for r in await conn.fetch(
            "SELECT activity_id FROM activities WHERE submission_id = ANY($1::uuid[])", sub_ids
        )]
        if act_ids:
            await conn.execute(
                "DELETE FROM output_indicators WHERE activity_id = ANY($1::uuid[])", act_ids
            )
        await conn.execute(
            "DELETE FROM activities WHERE submission_id = ANY($1::uuid[])", sub_ids
        )
        await conn.execute(
            "DELETE FROM audit_logs WHERE resource_id = ANY($1::uuid[])", sub_ids
        )
        n = await conn.fetchval(
            "DELETE FROM submissions WHERE id = ANY($1::uuid[]) RETURNING count(*)",
            sub_ids
        )
        # asyncpg returns None for DELETE without RETURNING count; count manually
        n_deleted = len(sub_ids)
        total_subs += n_deleted
        print(f"  ✓  Deleted {n_deleted} submissions for '{label}'")

    # ── Delete seed/pilot users ───────────────────────────────────────────────
    user_ids = [str(r["id"]) for r in await conn.fetch(
        "SELECT id FROM users WHERE email = ANY($1::text[])", SEED_USER_EMAILS
    )]
    if user_ids:
        await conn.execute(
            "DELETE FROM audit_logs WHERE user_id = ANY($1::uuid[])", user_ids
        )
        await conn.execute(
            "DELETE FROM token_blacklist WHERE user_id = ANY($1::uuid[])", user_ids
        )
        n_users = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE id = ANY($1::uuid[])", user_ids
        )
        await conn.execute(
            "DELETE FROM users WHERE id = ANY($1::uuid[])", user_ids
        )
        print(f"  ✓  Deleted {n_users} seed/pilot users")

    await conn.close()
    print(f"\nCleanup complete.")
    print(f"  Submissions removed : {total_subs}")
    print(f"  Users removed       : {len(user_ids) if user_ids else 0}")
    print("\nThe system is ready for production data.")


if __name__ == "__main__":
    asyncio.run(main())

"""
Create partner login accounts for the newly added organisations
(SEND SIERRA LEONE, FOCUS 1000), each linked to its organisation.

Run AFTER seed_new_partners.py (the organisations must exist first):
    python seed_new_partner_users.py

Safe to re-run — existing users are updated, not duplicated.

Default password: Pilot2026!  (override with PILOT_PASSWORD env var)
Ask each partner to change it via Profile Settings after first login.
"""
import asyncio
import os
import uuid
import asyncpg
from passlib.context import CryptContext

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub",
).replace("postgresql+asyncpg://", "postgresql://")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = os.getenv("PILOT_PASSWORD", "Pilot2026!")

# Primary focal person per organisation (matches the org contact in the directory)
PARTNER_USERS = [
    {
        "full_name": "Hassanatu Bah",
        "email":     "hassanatu@sendsierraleone.com",
        "org_name":  "SEND SIERRA LEONE",
    },
    {
        "full_name": "Mariama Awuko",
        "email":     "awukumariama@gmail.com",
        "org_name":  "FOCUS 1000",
    },
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    print(f"Creating {len(PARTNER_USERS)} partner accounts...\n")

    for u in PARTNER_USERS:
        org_id = await conn.fetchval(
            "SELECT org_id FROM organisations WHERE org_name = $1", u["org_name"]
        )
        if not org_id:
            print(f"  ✗  Organisation not found: {u['org_name']} — run seed_new_partners.py first")
            continue

        password_hash = pwd_context.hash(DEFAULT_PASSWORD)
        existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", u["email"])
        if existing:
            await conn.execute(
                """UPDATE users
                   SET password_hash = $1, full_name = $2, role = 'partner',
                       organisation_id = $3, is_active = true
                   WHERE email = $4""",
                password_hash, u["full_name"], str(org_id), u["email"],
            )
            print(f"  ↻  Updated  {u['email']} ({u['org_name']})")
        else:
            await conn.execute(
                """INSERT INTO users
                       (id, email, password_hash, full_name, role,
                        organisation_id, is_active, email_verified)
                   VALUES ($1, $2, $3, $4, 'partner', $5, true, true)""",
                str(uuid.uuid4()), u["email"], password_hash,
                u["full_name"], str(org_id),
            )
            print(f"  ✓  Created  {u['email']} ({u['org_name']})")

    await conn.close()
    print(f"\nDone. Default password: {DEFAULT_PASSWORD}")
    print("Ask each partner to change their password after first login.")


if __name__ == "__main__":
    asyncio.run(main())

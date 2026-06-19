"""
Creates five pilot partner user accounts, each linked to a different
organisation. These are the logins for the pilot launch.

Run from backend/ directory:
    python seed_pilot_users.py

Safe to re-run — existing users are updated, not duplicated.

Default password for all pilot users: Pilot2026!
Change passwords via Profile Settings after first login.
"""
import asyncio
import os
import uuid
import asyncpg
from passlib.context import CryptContext

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEFAULT_PASSWORD = os.getenv("PILOT_PASSWORD", "Pilot2026!")

PILOT_USERS = [
    {
        "full_name": "Salaymatu Kamara",
        "email":     "s.kamara@plan-international.org",
        "org_name":  "Plan International",
    },
    {
        "full_name": "Ibrahim Koroma",
        "email":     "i.koroma@savethechildren.org",
        "org_name":  "Save the Children SL",
    },
    {
        "full_name": "Mohamed Conteh",
        "email":     "m.conteh@streetchildsl.org",
        "org_name":  "Street Child of Sierra Leone",
    },
    {
        "full_name": "Hawa Jalloh",
        "email":     "h.jalloh@worldvision.org",
        "org_name":  "World Vision SL",
    },
    {
        "full_name": "Valerie Momoh",
        "email":     "v.momoh@actionaid.org",
        "org_name":  "ActionAid Sierra Leone",
    },
]


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    print(f"Creating {len(PILOT_USERS)} pilot partner accounts...\n")

    for u in PILOT_USERS:
        # Resolve organisation ID
        org_id = await conn.fetchval(
            "SELECT org_id FROM organisations WHERE org_name = $1", u["org_name"]
        )
        if not org_id:
            print(f"  ✗  Organisation not found: {u['org_name']} — run seed_organisations.py first")
            continue

        password_hash = pwd_context.hash(DEFAULT_PASSWORD)

        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1", u["email"]
        )
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
            user_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO users
                       (id, email, password_hash, full_name, role,
                        organisation_id, is_active, email_verified)
                   VALUES ($1, $2, $3, $4, 'partner', $5, true, true)""",
                user_id, u["email"], password_hash,
                u["full_name"], str(org_id),
            )
            print(f"  ✓  Created  {u['email']} ({u['org_name']})")

    await conn.close()

    print(f"\nPilot logins created.")
    print(f"Default password: {DEFAULT_PASSWORD}")
    print("Ask each partner to change their password after first login.")
    print("\nSummary:")
    for u in PILOT_USERS:
        print(f"  {u['email']:45s}  {u['org_name']}")


if __name__ == "__main__":
    asyncio.run(main())

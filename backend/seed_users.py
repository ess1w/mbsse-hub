"""
Creates (or updates) the default partner and viewer demo users.
Uses asyncpg directly (no SQLAlchemy).

Run from backend/ directory:
    python seed_users.py

Docker:
    docker exec -it mbsse_backend python seed_users.py

Environment overrides:
    PARTNER_EMAIL, PARTNER_PASSWORD, PARTNER_FULLNAME
    VIEWER_EMAIL,  VIEWER_PASSWORD,  VIEWER_FULLNAME
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


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


USERS = [
    {
        "email":     os.getenv("PARTNER_EMAIL",    "partner@mbsse.gov.sl"),
        "password":  os.getenv("PARTNER_PASSWORD", "changeme123"),
        "full_name": os.getenv("PARTNER_FULLNAME", "Demo Partner User"),
        "role":      "partner",
    },
    {
        "email":     os.getenv("VIEWER_EMAIL",    "viewer@mbsse.gov.sl"),
        "password":  os.getenv("VIEWER_PASSWORD", "changeme123"),
        "full_name": os.getenv("VIEWER_FULLNAME", "Demo Viewer User"),
        "role":      "viewer",
    },
]


async def upsert_user(conn, user: dict, org_id=None) -> None:
    email    = user["email"]
    password = user["password"]
    role     = user["role"]
    # Partners are linked to an organisation so they can submit reports.
    org = org_id if role == "partner" else None

    existing = await conn.fetchval(
        "SELECT id FROM users WHERE email = $1", email
    )
    if existing:
        await conn.execute(
            "UPDATE users SET password_hash = $1, role = $2, organisation_id = $3 WHERE email = $4",
            hash_password(password), role, org, email,
        )
        print(f"✓ [{role}] {email} — updated" + (f" (org linked)" if org else "") + ".")
    else:
        user_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO users
                   (id, email, password_hash, full_name, role, organisation_id, is_active, email_verified)
               VALUES ($1, $2, $3, $4, $5, $6, true, true)""",
            user_id, email, hash_password(password), user["full_name"], role, org,
        )
        print(f"✓ [{role}] {email} — created" + (f" (org linked)" if org else "") + ".")

    print(f"  Password : {password}")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Pick a stable organisation to attribute the demo partner's reports to.
        partner_org = await conn.fetchval(
            "SELECT org_id FROM organisations ORDER BY org_name LIMIT 1"
        )
        if partner_org is None:
            print("⚠ No organisations found — run seed_organisations.py first; partner will be unlinked.")
        for user in USERS:
            await upsert_user(conn, user, org_id=partner_org)
    finally:
        await conn.close()

    print("\nChange passwords after first login!")


if __name__ == "__main__":
    asyncio.run(main())

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


async def upsert_user(conn, user: dict) -> None:
    email    = user["email"]
    password = user["password"]
    role     = user["role"]

    existing = await conn.fetchval(
        "SELECT id FROM users WHERE email = $1", email
    )
    if existing:
        await conn.execute(
            "UPDATE users SET password_hash = $1, role = $2 WHERE email = $3",
            hash_password(password), role, email,
        )
        print(f"✓ [{role}] {email} — password hash updated.")
    else:
        user_id = str(uuid.uuid4())
        await conn.execute(
            """INSERT INTO users
                   (id, email, password_hash, full_name, role, is_active, email_verified)
               VALUES ($1, $2, $3, $4, $5, true, true)""",
            user_id, email, hash_password(password), user["full_name"], role,
        )
        print(f"✓ [{role}] {email} — created.")

    print(f"  Password : {password}")


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for user in USERS:
            await upsert_user(conn, user)
    finally:
        await conn.close()

    print("\nChange passwords after first login!")


if __name__ == "__main__":
    asyncio.run(main())

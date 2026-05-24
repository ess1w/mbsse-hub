"""
Creates an admin user in the database.
Uses asyncpg directly (no SQLAlchemy) to avoid greenlet dependency.

Run from backend/ directory:
    python seed_admin.py

Docker:
    docker exec -it mbsse_backend python seed_admin.py
"""
import asyncio
import os
import uuid
import bcrypt
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mbsse:mbsse_secret@localhost:5432/mbsse_hub"
).replace("postgresql+asyncpg://", "postgresql://")

EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@mbsse.gov.sl")
PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")
FULLNAME = os.getenv("ADMIN_FULLNAME", "MBSSE Administrator")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


async def main():
    conn = await asyncpg.connect(DATABASE_URL)

    existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", EMAIL)
    if existing:
        print(f"User {EMAIL} already exists — skipping.")
        await conn.close()
        return

    user_id = str(uuid.uuid4())
    await conn.execute(
        """INSERT INTO users (id, email, password_hash, full_name, role, is_active, email_verified)
           VALUES ($1, $2, $3, $4, 'admin', true, true)""",
        user_id, EMAIL, hash_password(PASSWORD), FULLNAME,
    )
    await conn.close()

    print("✓ Admin user created")
    print(f"  Email:    {EMAIL}")
    print(f"  Password: {PASSWORD}")
    print(f"  ID:       {user_id}")
    print()
    print("  Change the password after first login!")


if __name__ == "__main__":
    asyncio.run(main())

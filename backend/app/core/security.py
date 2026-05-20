"""
JWT creation/verification and password hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Passwords ────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Tokens ───────────────────────────────────────────────────────────────────

def _make_token(
    subject: str,
    kind: Literal["access", "refresh"],
    extra: dict | None = None,
) -> str:
    if kind == "access":
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )

    payload = {
        "sub": subject,        # user UUID (str)
        "kind": kind,
        "jti": str(uuid4()),   # unique token ID (for blacklisting)
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: str, role: str, org_id: str | None = None) -> str:
    return _make_token(
        user_id,
        "access",
        extra={"role": role, "org_id": org_id},
    )


def create_refresh_token(user_id: str) -> str:
    return _make_token(user_id, "refresh")


def decode_token(token: str) -> dict:
    """
    Raises jose.JWTError on invalid / expired token.
    Caller is responsible for also checking token_blacklist.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

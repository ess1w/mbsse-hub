"""
FastAPI dependency injection: DB session, current user, role guards.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist

bearer = HTTPBearer()


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = creds.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("kind") != "access":
            raise credentials_exc
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not user_id or not jti:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # Check blacklist (logout / password-reset invalidation)
    blacklisted = await db.scalar(
        select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    )
    if blacklisted:
        raise credentials_exc

    user = await db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise credentials_exc
    return user


# ── Role guards (use as FastAPI dependencies) ─────────────────────────────────

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_admin_or_viewer(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "viewer"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


def require_any(user: User = Depends(get_current_user)) -> User:
    """All authenticated roles are accepted."""
    return user


def partner_sees_own_only(
    org_id: UUID,
    user: User = Depends(get_current_user),
) -> None:
    """
    Partners can only access resources belonging to their own organisation.
    Admins and viewers are unrestricted.
    """
    if user.role == "partner" and user.organisation_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")

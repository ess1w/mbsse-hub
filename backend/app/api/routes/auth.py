"""
POST /auth/login          → access + refresh tokens
POST /auth/refresh        → new access token
POST /auth/logout         → blacklist current token
POST /auth/password-reset → request reset email
POST /auth/password-reset/confirm
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.session import get_db
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    db.add(user)

    return TokenResponse(
        access_token=create_access_token(
            str(user.id), user.role, str(user.organisation_id) if user.organisation_id else None
        ),
        refresh_token=create_refresh_token(str(user.id)),
        role=user.role,
        full_name=user.full_name,
        organisation_id=str(user.organisation_id) if user.organisation_id else None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("kind") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload["sub"]
        jti = payload["jti"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    blacklisted = await db.scalar(
        select(TokenBlacklist).where(TokenBlacklist.jti == jti)
    )
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(
            str(user.id), user.role, str(user.organisation_id) if user.organisation_id else None
        ),
        refresh_token=create_refresh_token(str(user.id)),
        role=user.role,
        full_name=user.full_name,
        organisation_id=str(user.organisation_id) if user.organisation_id else None,
    )


@router.post("/logout", status_code=204)
async def logout(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(creds.credentials)
        jti = payload["jti"]
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    except JWTError:
        return  # already invalid; nothing to blacklist

    db.add(TokenBlacklist(jti=jti, expires_at=exp))

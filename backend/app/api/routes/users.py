"""
Admin user management — list + create/edit/deactivate/reactivate/delete/resend.

All endpoints are admin-only. The shapes returned match the User Management
screen (name/org/status/invitePending) so the frontend can use them directly.

New users are created with a default password (NEW_USER_PASSWORD); share it with
the user and ask them to change it via Profile Settings after first login.
"""
import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.organisation import Organisation
from app.models.user import User
from app.services.audit import log_action
from app.services.email import send_email

logger = logging.getLogger(__name__)
router = APIRouter(tags=["users"])

NEW_USER_PASSWORD = os.getenv("NEW_USER_PASSWORD", "Welcome2026!")
ROLES = {"admin", "viewer", "partner", "gem_coordinator"}


def _build_invite_email(name: str, email: str, frontend_url: str) -> tuple[str, str]:
    subject = "[MBSSE Hub] You've been invited to the SRGBV Coordination Hub"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;color:#1a1a2e">
      <div style="background:#1F5C99;padding:16px 24px;border-radius:8px 8px 0 0">
        <span style="color:#fff;font-size:16px;font-weight:600">MBSSE SRGBV Coordination Hub</span>
      </div>
      <div style="background:#fff;padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px">
        <p>Dear {name},</p>
        <p>An account has been created for you on the MBSSE SRGBV Coordination Hub.</p>
        <p><strong>Email:</strong> {email}<br/>
           <strong>Temporary password:</strong> {NEW_USER_PASSWORD}</p>
        <p style="margin:24px 0">
          <a href="{frontend_url}" style="background:#1F5C99;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:500">
            Log in to the Hub →
          </a>
        </p>
        <p>For your security, please change your password from Profile Settings after your first login.</p>
        <hr style="border:none;border-top:1px solid #f1f5f9;margin:20px 0"/>
        <p style="font-size:11px;color:#94a3b8">
          Ministry of Basic and Senior Secondary Education, Sierra Leone<br/>SRGBV Coordination Hub
        </p>
      </div>
    </div>
    """
    return subject, html


async def _send_invite(user: User) -> None:
    """Best-effort invite email — never fails the surrounding request."""
    try:
        subject, html = _build_invite_email(
            user.full_name, user.email, get_settings().frontend_url
        )
        await send_email(to=user.email, subject=subject, html_body=html)
    except Exception as exc:
        logger.error("Invite email to %s failed: %s", user.email, exc)


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserCreateIn(BaseModel):
    name: str
    email: str
    role: str
    org: str | None = None          # organisation name (partner users)
    send_invite: bool = True


class UserUpdateIn(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    org: str | None = None


def _serialize(u: User) -> dict:
    return {
        "id": str(u.id),
        "name": u.full_name,
        "email": u.email,
        "role": u.role,
        "org": u.organisation.org_name if u.organisation else None,
        "status": "Active" if u.is_active else "Inactive",
        "lastLogin": u.last_login.isoformat() if u.last_login else None,
        "invitePending": not u.email_verified,
    }


async def _get_or_404(user_id: UUID, db: AsyncSession) -> User:
    u = (
        await db.scalars(
            select(User).options(joinedload(User.organisation)).where(User.id == user_id)
        )
    ).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


async def _resolve_org(org_name: str | None, db: AsyncSession) -> UUID | None:
    if not org_name:
        return None
    org_id = await db.scalar(
        select(Organisation.org_id).where(Organisation.org_name == org_name)
    )
    if not org_id:
        raise HTTPException(status_code=404, detail=f"Organisation not found: {org_name}")
    return org_id


def _validate_role(role: str) -> None:
    if role not in ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role: {role}")


# ── List ────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    rows = (
        await db.scalars(
            select(User).options(joinedload(User.organisation)).order_by(User.full_name)
        )
    ).unique().all()
    return [_serialize(u) for u in rows]


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/users", status_code=201)
async def create_user(
    body: UserCreateIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    _validate_role(body.role)
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=422, detail="A valid email address is required")
    if body.role == "partner" and not body.org:
        raise HTTPException(status_code=422, detail="Partner users must be linked to an organisation")
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="This email is already registered")

    org_id = await _resolve_org(body.org if body.role == "partner" else None, db)

    user = User(
        email=email,
        full_name=body.name.strip(),
        role=body.role,
        organisation_id=org_id,
        password_hash=hash_password(NEW_USER_PASSWORD),
        is_active=True,
        email_verified=not body.send_invite,   # pending invite => not yet verified
    )
    db.add(user)
    await db.flush()
    await log_action(db, admin, "user.create", "user", user.id)
    if body.send_invite:
        await _send_invite(user)
    return _serialize(await _get_or_404(user.id, db))


# ── Update ────────────────────────────────────────────────────────────────────

@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    body: UserUpdateIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    u = await _get_or_404(user_id, db)

    if body.name is not None:
        u.full_name = body.name.strip()
    if body.email is not None:
        email = body.email.strip().lower()
        if "@" not in email:
            raise HTTPException(status_code=422, detail="A valid email address is required")
        clash = await db.scalar(
            select(User.id).where(User.email == email, User.id != u.id)
        )
        if clash:
            raise HTTPException(status_code=409, detail="This email is already registered")
        u.email = email
    if body.role is not None:
        _validate_role(body.role)
        u.role = body.role
    # Organisation: only partners keep one
    role = body.role if body.role is not None else u.role
    if role == "partner":
        if body.org is not None:
            u.organisation_id = await _resolve_org(body.org, db)
    else:
        u.organisation_id = None

    await db.flush()
    await log_action(db, admin, "user.update", "user", u.id)
    return _serialize(await _get_or_404(u.id, db))


# ── Status ────────────────────────────────────────────────────────────────────

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    u = await _get_or_404(user_id, db)
    u.is_active = False
    await db.flush()
    await log_action(db, admin, "user.deactivate", "user", u.id)
    return _serialize(u)


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    u = await _get_or_404(user_id, db)
    u.is_active = True
    await db.flush()
    await log_action(db, admin, "user.reactivate", "user", u.id)
    return _serialize(u)


@router.post("/users/{user_id}/resend-invite")
async def resend_invite(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    u = await _get_or_404(user_id, db)
    u.email_verified = False
    await db.flush()
    # Surface delivery errors here (unlike create, which is best-effort) so the
    # admin can see exactly why an email failed.
    try:
        subject, html = _build_invite_email(u.full_name, u.email, get_settings().frontend_url)
        await send_email(to=u.email, subject=subject, html_body=html)
    except Exception as exc:
        logger.error("Resend invite to %s failed: %s", u.email, exc)
        raise HTTPException(status_code=502, detail=f"Email delivery failed: {exc}")
    await log_action(db, admin, "user.resend_invite", "user", u.id)
    return _serialize(u)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    u = await _get_or_404(user_id, db)
    await log_action(db, admin, "user.delete", "user", u.id)
    await db.delete(u)

"""
Read-only user listing for the admin User Management screen.

GET /api/v1/users  → list all users with their organisation name and status
(admin only). Write operations (create/edit/deactivate) are not yet wired.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["users"])


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        await db.scalars(
            select(User).options(joinedload(User.organisation)).order_by(User.full_name)
        )
    ).unique().all()

    return [
        {
            "id": str(u.id),
            "name": u.full_name,
            "email": u.email,
            "role": u.role,
            "org": u.organisation.org_name if u.organisation else None,
            "status": "Active" if u.is_active else "Inactive",
            "lastLogin": u.last_login.isoformat() if u.last_login else None,
            "invitePending": not u.email_verified,
        }
        for u in rows
    ]

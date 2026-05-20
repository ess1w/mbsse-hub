from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.models.user import User


async def log_action(
    db: AsyncSession,
    user: User,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    diff: dict | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        diff=diff,
        ip_address=ip_address,
    ))

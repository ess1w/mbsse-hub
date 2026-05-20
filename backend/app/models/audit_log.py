import uuid
from sqlalchemy import Column, ForeignKey, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(60), nullable=False)       # e.g. 'submission.submit'
    resource_type = Column(String(60), nullable=False) # e.g. 'submission'
    resource_id = Column(UUID(as_uuid=True))
    diff = Column(JSONB)                               # {before: {}, after: {}}
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(TIMESTAMPTZ, server_default=func.now())

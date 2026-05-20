"""
Project Registry — matches Section 5.2 of the data dictionary.
Multi-select fields (objective, tactic, focus_area, gov_counterpart) stored as PostgreSQL ARRAY.
"""
import uuid
from sqlalchemy import Column, Date, ForeignKey, Numeric, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.models.base import Base

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class Project(Base):
    __tablename__ = "projects"

    # 5.2 fields (canonical names)
    project_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id           = Column(UUID(as_uuid=True), ForeignKey("organisations.org_id", ondelete="CASCADE"), nullable=False)
    project_title    = Column(String(300), nullable=False)
    project_start    = Column(Date)
    project_end      = Column(Date)

    # Multi-select arrays (controlled vocabularies from Section 5.4)
    objective        = Column(ARRAY(String), nullable=False, default=list)   # obj1 / obj2 / obj3
    tactic           = Column(ARRAY(String), nullable=False, default=list)   # tac1 … tac9
    focus_area       = Column(ARRAY(String), nullable=False, default=list)   # fa1 … fa8

    activity_summary = Column(Text)
    funding_source   = Column(String(300))
    budget_usd       = Column(Numeric(14, 2))
    budget_currency  = Column(String(3), default="USD")                      # USD / SLE
    gov_counterpart  = Column(ARRAY(String), default=list)                   # MoGCA / MSW / etc.
    key_partners     = Column(Text)

    # Extra admin field for dashboard display
    project_status   = Column(String(20), default="Active")                  # Active / Closed / Planned

    created_at = Column(TIMESTAMPTZ, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, server_default=func.now(), onupdate=func.now())

    # relationships
    organisation = relationship("Organisation", back_populates="projects")
    submissions  = relationship("Submission", back_populates="project")

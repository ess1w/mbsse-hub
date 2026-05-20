# Import all models so Alembic can detect them
from app.models.base import Base
from app.models.location import District, Chiefdom
from app.models.organisation import Organisation
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.models.project import Project
from app.models.reporting_period import ReportingPeriod
from app.models.submission import Submission, SubmissionLocation, Activity, OutputIndicators
from app.models.uploaded_file import UploadedFile
from app.models.reminder import Reminder
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "District", "Chiefdom",
    "Organisation",
    "User", "TokenBlacklist",
    "Project",
    "ReportingPeriod",
    "Submission", "SubmissionLocation", "Activity", "OutputIndicators",
    "UploadedFile",
    "Reminder",
    "AuditLog",
]

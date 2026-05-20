from uuid import UUID
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, field_validator
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Literal["admin", "viewer", "partner"] = "partner"
    organisation_id: UUID | None = None

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a digit")
        return v

    @field_validator("full_name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be blank")
        return v.strip()


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    organisation_id: UUID | None = None


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    full_name: str
    role: str
    organisation_id: UUID | None
    is_active: bool
    email_verified: bool
    last_login: datetime | None
    created_at: datetime

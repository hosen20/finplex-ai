from datetime import datetime

from app.domain.enums import UserRole
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreateRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.REVIEWER


class UserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
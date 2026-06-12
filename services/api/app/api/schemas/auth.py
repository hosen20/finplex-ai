from app.domain.enums import UserRole
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BootstrapAdminRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    full_name: str
    password: str


class AuthenticatedUserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
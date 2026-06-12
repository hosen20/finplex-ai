from datetime import datetime

from app.domain.enums import TenantStatus
from pydantic import BaseModel, ConfigDict


class TenantCreateRequest(BaseModel):
    name: str
    erp_provider: str = "local"
    crm_provider: str = "local"
    actor_user_id: str | None = None


class TenantActionRequest(BaseModel):
    actor_user_id: str


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    status: TenantStatus
    erp_provider: str
    crm_provider: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
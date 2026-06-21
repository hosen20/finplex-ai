from datetime import datetime

from app.domain.enums import TenantStatus
from pydantic import BaseModel, ConfigDict


class TenantCreateRequest(BaseModel):
    name: str
    erp_provider: str = "local"
    crm_provider: str = "local"


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    status: TenantStatus
    erp_provider: str
    crm_provider: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

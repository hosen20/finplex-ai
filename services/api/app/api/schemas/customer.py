from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerCreateRequest(BaseModel):
    tenant_id: str | None = None
    company_name: str
    contact_name: str
    contact_email: str
    preferred_contact_channel: str = "email"
    relationship_status: str = "normal"
    tags: list[str] = []


class CustomerResponse(BaseModel):
    customer_id: str
    tenant_id: str
    company_name: str
    contact_name: str
    contact_email: str
    preferred_contact_channel: str
    relationship_status: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from typing import Any

from app.domain.enums import InvoiceStatus, PaymentStatus
from pydantic import BaseModel, ConfigDict


class InvoiceCreateRequest(BaseModel):
    tenant_id: str
    actor_user_id: str
    file_name: str
    storage_key: str
    customer_id: str | None = None
    extracted_fields: dict[str, Any] | None = None


class InvoiceResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    uploaded_by_user_id: str
    customer_id: str | None = None
    file_name: str
    storage_key: str
    status: InvoiceStatus
    payment_status: PaymentStatus
    extracted_fields: dict[str, Any] | None = None
    evidence_ids: list[str]
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceUploadedEvent(BaseModel):
    """Kafka event emitted by the API after an invoice file is uploaded."""

    invoice_id: str
    tenant_id: str
    uploaded_by_user_id: str
    file_name: str
    storage_key: str
    content_type: str
    size_bytes: int = Field(ge=0)
    event_id: str
    event_type: str = "invoice.uploaded"
    occurred_at: datetime
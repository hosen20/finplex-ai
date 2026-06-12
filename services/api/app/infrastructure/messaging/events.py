from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class InvoiceUploadedEvent:
    """Event emitted after an invoice file is stored and registered."""

    invoice_id: str
    tenant_id: str
    uploaded_by_user_id: str
    file_name: str
    storage_key: str
    content_type: str
    size_bytes: int
    event_id: str
    event_type: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        invoice_id: str,
        tenant_id: str,
        uploaded_by_user_id: str,
        file_name: str,
        storage_key: str,
        content_type: str,
        size_bytes: int,
    ) -> "InvoiceUploadedEvent":
        return cls(
            event_id=f"evt_{uuid4().hex}",
            event_type="invoice.uploaded",
            invoice_id=invoice_id,
            tenant_id=tenant_id,
            uploaded_by_user_id=uploaded_by_user_id,
            file_name=file_name,
            storage_key=storage_key,
            content_type=content_type,
            size_bytes=size_bytes,
            occurred_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, str | int]:
        payload = asdict(self)
        payload["occurred_at"] = self.occurred_at.isoformat()
        return payload
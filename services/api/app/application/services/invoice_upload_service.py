from dataclasses import dataclass
from uuid import uuid4

from app.application.services.invoice_service import InvoiceService
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.messaging.event_publisher import EventPublisher
from app.infrastructure.messaging.events import InvoiceUploadedEvent
from app.infrastructure.storage.invoice_storage import InvoiceStorage
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class InvoiceUploadResult:
    """Result returned after an invoice file upload workflow completes."""

    invoice: InvoiceModel
    event: InvoiceUploadedEvent


class InvoiceUploadService:
    """Stores invoice files, records metadata, and emits upload events."""

    def __init__(
        self,
        *,
        session: Session,
        storage: InvoiceStorage,
        event_publisher: EventPublisher,
    ) -> None:
        self.session = session
        self.storage = storage
        self.event_publisher = event_publisher

    def upload_invoice_file(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
        customer_id: str | None = None,
    ) -> InvoiceUploadResult:
        if not content:
            raise ValueError("Invoice file cannot be empty.")

        invoice_id = f"inv_{uuid4().hex}"
        stored_file = self.storage.save_invoice(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            file_name=file_name,
            content_type=content_type,
            content=content,
        )

        invoice = InvoiceService(self.session).create_invoice_metadata(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            customer_id=customer_id,
            file_name=stored_file.file_name,
            storage_key=stored_file.storage_key,
            invoice_id=invoice_id,
        )

        event = InvoiceUploadedEvent.create(
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            uploaded_by_user_id=actor_user_id,
            file_name=stored_file.file_name,
            storage_key=stored_file.storage_key,
            content_type=stored_file.content_type,
            size_bytes=stored_file.size_bytes,
        )
        self.event_publisher.publish_invoice_uploaded(event)

        return InvoiceUploadResult(invoice=invoice, event=event)
from app.application.services.invoice_upload_service import InvoiceUploadService
from app.domain.enums import TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.messaging.events import InvoiceUploadedEvent
from app.infrastructure.storage.invoice_storage import StoredInvoiceFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


class FakeStorage:
    def __init__(self) -> None:
        self.saved_content: bytes | None = None

    def save_invoice(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> StoredInvoiceFile:
        self.saved_content = content
        return StoredInvoiceFile(
            storage_key=f"{tenant_id}/invoices/{invoice_id}/{file_name}",
            file_name=file_name,
            content_type=content_type,
            size_bytes=len(content),
        )


class FakePublisher:
    def __init__(self) -> None:
        self.published_event: InvoiceUploadedEvent | None = None

    def publish_invoice_uploaded(self, event: InvoiceUploadedEvent) -> None:
        self.published_event = event


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_tenant_and_user(session: Session) -> None:
    session.add(
        TenantModel(
            tenant_id="tenant_upload",
            name="Upload Tenant",
            status=TenantStatus.ACTIVE,
            erp_provider="local",
            crm_provider="local",
        )
    )
    session.add(
        UserModel(
            user_id="user_upload_admin",
            tenant_id="tenant_upload",
            email="upload-admin@example.com",
            full_name="Upload Admin",
            hashed_password="not-real",
            role=UserRole.TENANT_ADMIN,
            is_active=True,
        )
    )
    session.commit()


def test_upload_invoice_file_stores_metadata_and_publishes_event() -> None:
    with make_session() as session:
        seed_tenant_and_user(session)
        storage = FakeStorage()
        publisher = FakePublisher()

        result = InvoiceUploadService(
            session=session,
            storage=storage,
            event_publisher=publisher,
        ).upload_invoice_file(
            tenant_id="tenant_upload",
            actor_user_id="user_upload_admin",
            file_name="invoice.pdf",
            content_type="application/pdf",
            content=b"fake-pdf-content",
        )

        assert result.invoice.invoice_id.startswith("inv_")
        assert result.invoice.storage_key.endswith("invoice.pdf")
        assert storage.saved_content == b"fake-pdf-content"
        assert publisher.published_event is not None
        assert publisher.published_event.invoice_id == result.invoice.invoice_id
        assert publisher.published_event.event_type == "invoice.uploaded"
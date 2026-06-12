from collections.abc import Generator

from app.database import get_db_session
from app.domain.enums import TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.messaging.event_publisher import get_event_publisher
from app.infrastructure.messaging.events import InvoiceUploadedEvent
from app.infrastructure.storage.invoice_storage import (
    StoredInvoiceFile,
    get_invoice_storage,
)
from app.main import app
from app.security import hash_password
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)


class RouteFakeStorage:
    def save_invoice(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> StoredInvoiceFile:
        return StoredInvoiceFile(
            storage_key=f"{tenant_id}/invoices/{invoice_id}/{file_name}",
            file_name=file_name,
            content_type=content_type,
            size_bytes=len(content),
        )


class RouteFakePublisher:
    def __init__(self) -> None:
        self.events: list[InvoiceUploadedEvent] = []

    def publish_invoice_uploaded(self, event: InvoiceUploadedEvent) -> None:
        self.events.append(event)


publisher = RouteFakePublisher()


def override_get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def use_upload_route_test_dependencies() -> None:
    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_invoice_storage] = RouteFakeStorage
    app.dependency_overrides[get_event_publisher] = lambda: publisher


client = TestClient(app)


def seed_upload_route_data() -> None:
    use_upload_route_test_dependencies()

    with Session(engine) as session:
        if session.get(TenantModel, "tenant_upload_route") is not None:
            return

        session.add(
            TenantModel(
                tenant_id="tenant_upload_route",
                name="Upload Route Tenant",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            )
        )
        session.add(
            UserModel(
                user_id="user_upload_route_admin",
                tenant_id="tenant_upload_route",
                email="upload-route-admin@example.com",
                full_name="Upload Route Admin",
                hashed_password=hash_password("password123"),
                role=UserRole.TENANT_ADMIN,
                is_active=True,
            )
        )
        session.commit()


def auth_headers() -> dict[str, str]:
    seed_upload_route_data()
    use_upload_route_test_dependencies()

    response = client.post(
        "/auth/login",
        json={
            "email": "upload-route-admin@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_invoice_route_returns_invoice_and_event() -> None:
    use_upload_route_test_dependencies()

    response = client.post(
        "/invoices/upload",
        headers=auth_headers(),
        data={"tenant_id": "tenant_upload_route"},
        files={"file": ("invoice.pdf", b"fake-pdf-content", "application/pdf")},
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["invoice"]["invoice_id"].startswith("inv_")
    assert body["invoice"]["storage_key"].endswith("invoice.pdf")
    assert body["event_type"] == "invoice.uploaded"
    assert body["event_topic"] == "invoice.uploaded"
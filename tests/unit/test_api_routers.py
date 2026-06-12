from collections.abc import Generator

from app.database import get_db_session
from app.domain.enums import TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from app.main import app
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


def override_get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session
client = TestClient(app)


def seed_router_data() -> None:
    with Session(engine) as session:
        existing = session.get(TenantModel, "tenant_router")
        if existing is not None:
            return

        session.add(
            TenantModel(
                tenant_id="tenant_router",
                name="Router Tenant",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            )
        )
        session.add(
            UserModel(
                user_id="user_router_admin",
                tenant_id="tenant_router",
                email="router-admin@example.com",
                full_name="Router Admin",
                hashed_password="not-real",
                role=UserRole.TENANT_ADMIN,
                is_active=True,
            )
        )
        session.commit()


def test_create_customer_route() -> None:
    seed_router_data()

    response = client.post(
        "/customers",
        json={
            "tenant_id": "tenant_router",
            "actor_user_id": "user_router_admin",
            "company_name": "Router Customer",
            "contact_name": "Hussein",
            "contact_email": "hussein@example.com",
            "tags": ["demo"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"].startswith("cust_")
    assert body["company_name"] == "Router Customer"


def test_create_invoice_route() -> None:
    seed_router_data()

    response = client.post(
        "/invoices",
        json={
            "tenant_id": "tenant_router",
            "actor_user_id": "user_router_admin",
            "file_name": "invoice.pdf",
            "storage_key": "tenant_router/invoices/invoice.pdf",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["invoice_id"].startswith("inv_")
    assert body["status"] == "uploaded"
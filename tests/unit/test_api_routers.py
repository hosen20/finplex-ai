from collections.abc import Generator

from app.database import get_db_session
from app.domain.enums import TenantStatus, UserRole
from app.infrastructure.db.models import Base
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
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


def override_get_db_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def use_router_test_db() -> None:
    app.dependency_overrides[get_db_session] = override_get_db_session


client = TestClient(app)


def seed_router_data() -> None:
    use_router_test_db()

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
                hashed_password=hash_password("password123"),
                role=UserRole.TENANT_ADMIN,
                is_active=True,
            )
        )
        session.commit()


def auth_headers() -> dict[str, str]:
    seed_router_data()
    use_router_test_db()

    response = client.post(
        "/auth/login",
        json={
            "email": "router-admin@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200, response.json()

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_customer_route_requires_auth() -> None:
    seed_router_data()
    use_router_test_db()

    response = client.post(
        "/customers",
        json={
            "tenant_id": "tenant_router",
            "company_name": "Router Customer",
            "contact_name": "Hussein",
            "contact_email": "hussein@example.com",
            "tags": ["demo"],
        },
    )

    assert response.status_code == 401


def test_create_customer_route() -> None:
    use_router_test_db()

    response = client.post(
        "/customers",
        headers=auth_headers(),
        json={
            "tenant_id": "tenant_router",
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
    use_router_test_db()

    response = client.post(
        "/invoices",
        headers=auth_headers(),
        json={
            "tenant_id": "tenant_router",
            "file_name": "invoice.pdf",
            "storage_key": "tenant_router/invoices/invoice.pdf",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["invoice_id"].startswith("inv_")
    assert body["status"] == "uploaded"
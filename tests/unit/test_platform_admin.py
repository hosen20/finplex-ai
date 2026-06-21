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


def use_platform_admin_test_db() -> None:
    app.dependency_overrides[get_db_session] = override_get_db_session


client = TestClient(app)


def seed_platform_admin_data() -> None:
    use_platform_admin_test_db()

    with Session(engine) as session:
        if session.get(TenantModel, "tenant_platform") is None:
            session.add(
                TenantModel(
                    tenant_id="tenant_platform",
                    name="Finplex Platform Operations",
                    status=TenantStatus.ACTIVE,
                    erp_provider="internal",
                    crm_provider="internal",
                )
            )

        if session.get(TenantModel, "tenant_customer") is None:
            session.add(
                TenantModel(
                    tenant_id="tenant_customer",
                    name="Customer Tenant",
                    status=TenantStatus.ACTIVE,
                    erp_provider="local",
                    crm_provider="local",
                )
            )

        if session.get(UserModel, "user_platform_admin") is None:
            session.add(
                UserModel(
                    user_id="user_platform_admin",
                    tenant_id="tenant_platform",
                    email="platform-admin@example.com",
                    full_name="Platform Admin",
                    hashed_password=hash_password("password123"),
                    role=UserRole.PLATFORM_ADMIN,
                    is_active=True,
                )
            )

        if session.get(UserModel, "user_tenant_admin") is None:
            session.add(
                UserModel(
                    user_id="user_tenant_admin",
                    tenant_id="tenant_customer",
                    email="tenant-admin@example.com",
                    full_name="Tenant Admin",
                    hashed_password=hash_password("password123"),
                    role=UserRole.TENANT_ADMIN,
                    is_active=True,
                )
            )

        session.commit()


def login_headers(email: str) -> dict[str, str]:
    seed_platform_admin_data()
    use_platform_admin_test_db()

    response = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )

    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_platform_admin_can_create_tenant() -> None:
    response = client.post(
        "/tenants",
        headers=login_headers("platform-admin@example.com"),
        json={
            "name": "New Customer Tenant",
            "erp_provider": "local",
            "crm_provider": "local",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["tenant_id"].startswith("tenant_")
    assert body["name"] == "New Customer Tenant"


def test_tenant_admin_cannot_create_tenant() -> None:
    response = client.post(
        "/tenants",
        headers=login_headers("tenant-admin@example.com"),
        json={
            "name": "Forbidden Tenant",
            "erp_provider": "local",
            "crm_provider": "local",
        },
    )

    assert response.status_code == 403


def test_platform_admin_can_create_first_tenant_admin() -> None:
    response = client.post(
        "/users",
        headers=login_headers("platform-admin@example.com"),
        json={
            "tenant_id": "tenant_customer",
            "email": "first-admin@example.com",
            "full_name": "First Admin",
            "password": "password123",
            "role": "tenant_admin",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["tenant_id"] == "tenant_customer"
    assert body["role"] == "tenant_admin"

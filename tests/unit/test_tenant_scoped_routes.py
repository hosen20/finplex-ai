from collections.abc import Generator
from uuid import uuid4

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


app.dependency_overrides[get_db_session] = override_get_db_session
client = TestClient(app)


def seed_scope_data() -> None:
    app.dependency_overrides[get_db_session] = override_get_db_session
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        if session.get(TenantModel, "tenant_scope_a") is not None:
            return

        tenants = [
            TenantModel(
                tenant_id="tenant_scope_a",
                name="Tenant Scope A",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            ),
            TenantModel(
                tenant_id="tenant_scope_b",
                name="Tenant Scope B",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            ),
            TenantModel(
                tenant_id="tenant_platform_scope",
                name="Platform Scope",
                status=TenantStatus.ACTIVE,
                erp_provider="internal",
                crm_provider="internal",
            ),
        ]
        session.add_all(tenants)
        session.add_all(
            [
                UserModel(
                    user_id="user_scope_admin_a",
                    tenant_id="tenant_scope_a",
                    email="scope-admin-a@example.com",
                    full_name="Scope Admin A",
                    hashed_password=hash_password("password123"),
                    role=UserRole.TENANT_ADMIN,
                    is_active=True,
                ),
                UserModel(
                    user_id="user_scope_admin_b",
                    tenant_id="tenant_scope_b",
                    email="scope-admin-b@example.com",
                    full_name="Scope Admin B",
                    hashed_password=hash_password("password123"),
                    role=UserRole.TENANT_ADMIN,
                    is_active=True,
                ),
                UserModel(
                    user_id="user_scope_platform",
                    tenant_id="tenant_platform_scope",
                    email="scope-platform@example.com",
                    full_name="Scope Platform Admin",
                    hashed_password=hash_password("password123"),
                    role=UserRole.PLATFORM_ADMIN,
                    is_active=True,
                ),
            ]
        )
        session.commit()


def auth_headers(email: str) -> dict[str, str]:
    app.dependency_overrides[get_db_session] = override_get_db_session
    seed_scope_data()
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.json()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_tenant_user_create_customer_uses_token_tenant() -> None:
    response = client.post(
        "/customers",
        headers=auth_headers("scope-admin-a@example.com"),
        json={
            "company_name": "Scoped Customer",
            "contact_name": "Maya Haddad",
            "contact_email": "maya@example.com",
            "tags": ["local-product"],
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["tenant_id"] == "tenant_scope_a"
    assert body["company_name"] == "Scoped Customer"


def test_tenant_user_cannot_query_another_tenant() -> None:
    response = client.get(
        "/customers?tenant_id=tenant_scope_b",
        headers=auth_headers("scope-admin-a@example.com"),
    )

    assert response.status_code == 403
    assert "another tenant" in response.json()["detail"]


def test_platform_admin_must_specify_tenant_for_tenant_routes() -> None:
    response = client.get(
        "/users",
        headers=auth_headers("scope-platform@example.com"),
    )

    assert response.status_code == 400
    assert "tenant_id" in response.json()["detail"]


def test_platform_admin_can_create_user_for_requested_tenant() -> None:
    email = f"created-{uuid4().hex}@example.com"

    response = client.post(
        "/users",
        headers=auth_headers("scope-platform@example.com"),
        json={
            "tenant_id": "tenant_scope_b",
            "email": email,
            "full_name": "Created Reviewer",
            "password": "password123",
            "role": "reviewer",
        },
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["tenant_id"] == "tenant_scope_b"
    assert body["email"] == email

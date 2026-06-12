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


def use_auth_test_db() -> None:
    app.dependency_overrides[get_db_session] = override_get_db_session


client = TestClient(app)


def seed_auth_user() -> None:
    use_auth_test_db()

    with Session(engine) as session:
        if session.get(TenantModel, "tenant_auth") is not None:
            return

        session.add(
            TenantModel(
                tenant_id="tenant_auth",
                name="Auth Tenant",
                status=TenantStatus.ACTIVE,
                erp_provider="local",
                crm_provider="local",
            )
        )
        session.add(
            UserModel(
                user_id="user_auth_admin",
                tenant_id="tenant_auth",
                email="auth-admin@example.com",
                full_name="Auth Admin",
                hashed_password=hash_password("password123"),
                role=UserRole.TENANT_ADMIN,
                is_active=True,
            )
        )
        session.commit()


def test_login_returns_access_token_and_me_returns_user() -> None:
    seed_auth_user()
    use_auth_test_db()

    login_response = client.post(
        "/auth/login",
        json={
            "email": "auth-admin@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200, login_response.json()
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "auth-admin@example.com"


def test_login_rejects_invalid_password() -> None:
    seed_auth_user()
    use_auth_test_db()

    response = client.post(
        "/auth/login",
        json={
            "email": "auth-admin@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
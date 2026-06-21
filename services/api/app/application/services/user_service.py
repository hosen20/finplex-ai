from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.application.services.mappers import user_model_to_domain
from app.domain.enums import AuditAction, UserRole
from app.domain.exceptions import PermissionDeniedError
from app.domain.policies.tenant_policy import TenantPolicy
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.tenant_repository import TenantRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.security import hash_password
from sqlalchemy.orm import Session


class UserService:
    """Application workflows for users and local bootstrap."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tenants = TenantRepository(session)
        self.audit = AuditService(session)

    def bootstrap_tenant_admin(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        password: str,
    ) -> UserModel:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} was not found.")

        existing_users = self.users.list_by_tenant(tenant_id)
        if existing_users:
            raise PermissionDeniedError(
                f"Tenant {tenant_id} already has users. Bootstrap is disabled."
            )

        user = self._create_user_record(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password=password,
            role=UserRole.TENANT_ADMIN,
        )

        self.audit.record(
            tenant_id=tenant_id,
            action=AuditAction.USER_CREATED,
            actor_user_id=None,
            entity_type="user",
            entity_id=user.user_id,
            metadata={"email": email, "bootstrap": True},
        )

        self.session.commit()
        return user

    def create_user(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        password: str,
        role: UserRole,
        actor_user_id: str,
    ) -> UserModel:
        tenant = self.tenants.get(tenant_id)
        actor = self.users.get(actor_user_id)

        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} was not found.")
        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        TenantPolicy.ensure_can_manage_tenant(user_model_to_domain(actor), tenant_id)

        user = self._create_user_record(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password=password,
            role=role,
        )

        self.audit.record(
            tenant_id=tenant_id,
            action=AuditAction.USER_CREATED,
            actor_user_id=actor_user_id,
            entity_type="user",
            entity_id=user.user_id,
            metadata={"email": email, "role": role.value},
        )

        self.session.commit()
        return user

    def list_users(self, *, tenant_id: str, actor_user_id: str) -> list[UserModel]:
        actor = self.users.get(actor_user_id)

        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        actor_domain = user_model_to_domain(actor)
        TenantPolicy.ensure_same_tenant(actor_domain, tenant_id)

        if not actor_domain.can_manage_tenant and actor_domain.role != UserRole.AUDITOR:
            raise PermissionDeniedError(
                f"User {actor_user_id} cannot list users for tenant {tenant_id}."
            )

        return self.users.list_by_tenant(tenant_id)

    def _create_user_record(
        self,
        *,
        tenant_id: str,
        email: str,
        full_name: str,
        password: str,
        role: UserRole,
    ) -> UserModel:
        existing = self.users.get_by_email(email)
        if existing is not None:
            raise ValueError(f"User with email {email} already exists.")

        user = UserModel(
            user_id=f"user_{uuid4().hex}",
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        self.users.add(user)
        return user
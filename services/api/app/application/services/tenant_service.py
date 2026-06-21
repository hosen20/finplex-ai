from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.application.services.mappers import (
    tenant_model_to_domain,
    user_model_to_domain,
)
from app.domain.enums import AuditAction, TenantStatus
from app.domain.policies.tenant_policy import TenantPolicy
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.tenant_repository import TenantRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


class TenantService:
    """Application workflows for tenants."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.tenants = TenantRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def create_tenant(
        self,
        *,
        name: str,
        erp_provider: str = "local",
        crm_provider: str = "local",
        actor_user_id: str | None = None,
    ) -> TenantModel:
        tenant = TenantModel(
            tenant_id=f"tenant_{uuid4().hex}",
            name=name,
            status=TenantStatus.ACTIVE,
            erp_provider=erp_provider,
            crm_provider=crm_provider,
        )
        self.tenants.add(tenant)

        self.audit.record(
            tenant_id=tenant.tenant_id,
            action=AuditAction.TENANT_CREATED,
            actor_user_id=actor_user_id,
            entity_type="tenant",
            entity_id=tenant.tenant_id,
            metadata={"name": name},
        )

        self.session.commit()
        return tenant

    def create_tenant_as_platform_admin(
        self,
        *,
        name: str,
        erp_provider: str,
        crm_provider: str,
        actor_user_id: str,
    ) -> TenantModel:
        actor = self._get_user_or_raise(actor_user_id)
        TenantPolicy.ensure_can_manage_platform(user_model_to_domain(actor))

        return self.create_tenant(
            name=name,
            erp_provider=erp_provider,
            crm_provider=crm_provider,
            actor_user_id=actor_user_id,
        )

    def list_tenants(self) -> list[TenantModel]:
        return self.tenants.list_all()

    def list_tenants_as_platform_admin(
        self,
        *,
        actor_user_id: str,
    ) -> list[TenantModel]:
        actor = self._get_user_or_raise(actor_user_id)
        TenantPolicy.ensure_can_manage_platform(user_model_to_domain(actor))
        return self.list_tenants()

    def suspend_tenant(self, *, tenant_id: str, actor_user_id: str) -> TenantModel:
        tenant = self._get_tenant_or_raise(tenant_id)
        actor = self._get_user_or_raise(actor_user_id)

        TenantPolicy.ensure_can_manage_tenant(
            user_model_to_domain(actor),
            tenant.tenant_id,
        )

        domain_tenant = tenant_model_to_domain(tenant)
        domain_tenant.suspend()

        tenant.status = domain_tenant.status
        tenant.updated_at = domain_tenant.updated_at

        self.audit.record(
            tenant_id=tenant.tenant_id,
            action=AuditAction.TENANT_SUSPENDED,
            actor_user_id=actor_user_id,
            entity_type="tenant",
            entity_id=tenant.tenant_id,
        )

        self.session.commit()
        return tenant

    def reactivate_tenant(self, *, tenant_id: str, actor_user_id: str) -> TenantModel:
        tenant = self._get_tenant_or_raise(tenant_id)
        actor = self._get_user_or_raise(actor_user_id)

        TenantPolicy.ensure_can_manage_tenant(
            user_model_to_domain(actor),
            tenant.tenant_id,
        )

        domain_tenant = tenant_model_to_domain(tenant)
        domain_tenant.reactivate()

        tenant.status = domain_tenant.status
        tenant.updated_at = domain_tenant.updated_at

        self.audit.record(
            tenant_id=tenant.tenant_id,
            action=AuditAction.TENANT_REACTIVATED,
            actor_user_id=actor_user_id,
            entity_type="tenant",
            entity_id=tenant.tenant_id,
        )

        self.session.commit()
        return tenant

    def _get_tenant_or_raise(self, tenant_id: str) -> TenantModel:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} was not found.")
        return tenant

    def _get_user_or_raise(self, user_id: str) -> UserModel:
        user = self.users.get(user_id)
        if user is None:
            raise ValueError(f"User {user_id} was not found.")
        return user

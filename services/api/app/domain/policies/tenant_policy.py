from app.domain.entities.tenant import Tenant
from app.domain.entities.user import User
from app.domain.exceptions import CrossTenantAccessError, PermissionDeniedError


class TenantPolicy:
    """Tenant isolation and tenant lifecycle rules."""

    @staticmethod
    def ensure_tenant_is_active(tenant: Tenant) -> None:
        tenant.require_active()

    @staticmethod
    def ensure_same_tenant(actor: User, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id:
            raise CrossTenantAccessError(
                f"User {actor.user_id} cannot access tenant {tenant_id}."
            )

    @staticmethod
    def ensure_can_manage_tenant(actor: User, tenant_id: str) -> None:
        TenantPolicy.ensure_same_tenant(actor, tenant_id)

        if not actor.can_manage_tenant:
            raise PermissionDeniedError(
                f"User {actor.user_id} cannot manage tenant {tenant_id}."
            )
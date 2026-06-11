from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.enums import TenantStatus
from app.domain.exceptions import TenantDeletedError, TenantSuspendedError


@dataclass(slots=True)
class Tenant:
    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    erp_provider: str = "local"
    crm_provider: str = "local"
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    def require_active(self) -> None:
        if self.status == TenantStatus.SUSPENDED:
            raise TenantSuspendedError(f"Tenant {self.tenant_id} is suspended.")
        if self.status == TenantStatus.DELETED:
            raise TenantDeletedError(f"Tenant {self.tenant_id} is deleted.")

    def suspend(self) -> None:
        self.require_not_deleted()
        self.status = TenantStatus.SUSPENDED
        self.updated_at = datetime.now(UTC)

    def reactivate(self) -> None:
        self.require_not_deleted()
        self.status = TenantStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def mark_deleted(self) -> None:
        self.status = TenantStatus.DELETED
        self.updated_at = datetime.now(UTC)

    def require_not_deleted(self) -> None:
        if self.status == TenantStatus.DELETED:
            raise TenantDeletedError(f"Tenant {self.tenant_id} is deleted.")
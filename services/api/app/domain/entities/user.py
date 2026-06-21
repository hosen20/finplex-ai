from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.enums import UserRole


@dataclass(slots=True)
class User:
    user_id: str
    tenant_id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = datetime.now(UTC)

    @property
    def is_platform_admin(self) -> bool:
        return self.role == UserRole.PLATFORM_ADMIN

    @property
    def can_manage_platform(self) -> bool:
        return self.is_platform_admin

    @property
    def can_manage_tenant(self) -> bool:
        return self.role in {
            UserRole.PLATFORM_ADMIN,
            UserRole.TENANT_ADMIN,
            UserRole.MANAGER,
        }

    @property
    def can_review_drafts(self) -> bool:
        return self.role in {
            UserRole.PLATFORM_ADMIN,
            UserRole.TENANT_ADMIN,
            UserRole.MANAGER,
            UserRole.REVIEWER,
        }

    @property
    def can_view_audit_logs(self) -> bool:
        return self.role in {
            UserRole.PLATFORM_ADMIN,
            UserRole.TENANT_ADMIN,
            UserRole.MANAGER,
            UserRole.AUDITOR,
        }

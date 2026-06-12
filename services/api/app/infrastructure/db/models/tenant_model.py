from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import TenantStatus
from app.infrastructure.db.models.base import Base, TimestampMixin


class TenantModel(Base, TimestampMixin):
    __tablename__ = "tenants"

    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )
    erp_provider: Mapped[str] = mapped_column(String(64), default="local")
    crm_provider: Mapped[str] = mapped_column(String(64), default="local")
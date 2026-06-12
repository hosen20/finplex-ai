from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import AuditAction
from app.infrastructure.db.models.base import Base, TimestampMixin


class AuditEventModel(Base, TimestampMixin):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, native_enum=False),
        index=True,
        nullable=False,
    )
    actor_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON,
        default=dict,
    )
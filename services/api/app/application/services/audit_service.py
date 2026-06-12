from typing import Any
from uuid import uuid4

from app.domain.enums import AuditAction
from app.infrastructure.db.models.audit_model import AuditEventModel
from app.infrastructure.db.repositories.audit_repository import AuditRepository
from sqlalchemy.orm import Session


class AuditService:
    """Creates audit events for important tenant-scoped actions."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AuditRepository(session)

    def record(
        self,
        *,
        tenant_id: str,
        action: AuditAction,
        actor_user_id: str | None,
        entity_type: str,
        entity_id: str,
        trace_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            audit_event_id=f"audit_{uuid4().hex}",
            tenant_id=tenant_id,
            action=action,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            trace_id=trace_id or f"trace_{uuid4().hex}",
            metadata_json=metadata or {},
        )
        self.repository.add(event)
        return event
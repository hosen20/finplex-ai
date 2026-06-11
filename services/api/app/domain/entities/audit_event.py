from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.enums import AuditAction


@dataclass(slots=True)
class AuditEvent:
    audit_event_id: str
    tenant_id: str
    action: AuditAction
    actor_user_id: str | None
    entity_type: str
    entity_id: str
    trace_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = datetime.now(UTC)
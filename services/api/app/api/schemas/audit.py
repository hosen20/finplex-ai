from datetime import datetime
from typing import Any

from app.domain.enums import AuditAction
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    audit_event_id: str
    tenant_id: str
    action: AuditAction
    actor_user_id: str | None = None
    entity_type: str
    entity_id: str
    trace_id: str
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
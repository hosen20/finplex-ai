from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.audit_model import AuditEventModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditEventModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, AuditEventModel)

    def get(self, audit_event_id: str) -> AuditEventModel | None:
        return self.get_by_id(audit_event_id)

    def list_by_tenant(self, tenant_id: str, limit: int = 100) -> list[AuditEventModel]:
        statement = (
            select(AuditEventModel)
            .where(AuditEventModel.tenant_id == tenant_id)
            .order_by(AuditEventModel.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())
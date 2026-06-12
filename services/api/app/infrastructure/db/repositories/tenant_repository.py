from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class TenantRepository(BaseRepository[TenantModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TenantModel)

    def get(self, tenant_id: str) -> TenantModel | None:
        return self.get_by_id(tenant_id)

    def list_all(self) -> list[TenantModel]:
        statement = select(TenantModel).order_by(TenantModel.created_at.desc())
        return list(self.session.scalars(statement).all())
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.customer_model import CustomerModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[CustomerModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, CustomerModel)

    def get(self, customer_id: str) -> CustomerModel | None:
        return self.get_by_id(customer_id)

    def list_by_tenant(self, tenant_id: str) -> list[CustomerModel]:
        statement = select(CustomerModel).where(CustomerModel.tenant_id == tenant_id)
        return list(self.session.scalars(statement).all())
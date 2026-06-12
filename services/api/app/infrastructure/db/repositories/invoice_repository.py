from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class InvoiceRepository(BaseRepository[InvoiceModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, InvoiceModel)

    def get(self, invoice_id: str) -> InvoiceModel | None:
        return self.get_by_id(invoice_id)

    def list_by_tenant(self, tenant_id: str) -> list[InvoiceModel]:
        statement = (
            select(InvoiceModel)
            .where(InvoiceModel.tenant_id == tenant_id)
            .order_by(InvoiceModel.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def list_by_customer(self, tenant_id: str, customer_id: str) -> list[InvoiceModel]:
        statement = select(InvoiceModel).where(
            InvoiceModel.tenant_id == tenant_id,
            InvoiceModel.customer_id == customer_id,
        )
        return list(self.session.scalars(statement).all())
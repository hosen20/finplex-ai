from typing import Any
from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.application.services.mappers import (
    tenant_model_to_domain,
    user_model_to_domain,
)
from app.domain.enums import AuditAction, InvoiceStatus, PaymentStatus
from app.domain.policies.invoice_policy import InvoicePolicy
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.repositories.customer_repository import CustomerRepository
from app.infrastructure.db.repositories.invoice_repository import InvoiceRepository
from app.infrastructure.db.repositories.tenant_repository import TenantRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


class InvoiceService:
    """Application workflows for invoice metadata and processing state."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.invoices = InvoiceRepository(session)
        self.tenants = TenantRepository(session)
        self.users = UserRepository(session)
        self.customers = CustomerRepository(session)
        self.audit = AuditService(session)

    def create_invoice_metadata(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        file_name: str,
        storage_key: str,
        customer_id: str | None = None,
        extracted_fields: dict[str, Any] | None = None,
        invoice_id: str | None = None,
    ) -> InvoiceModel:
        tenant = self.tenants.get(tenant_id)
        actor = self.users.get(actor_user_id)

        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} was not found.")
        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        if customer_id is not None and self.customers.get(customer_id) is None:
            raise ValueError(f"Customer {customer_id} was not found.")

        InvoicePolicy.ensure_can_upload(
            user_model_to_domain(actor),
            tenant_model_to_domain(tenant),
        )

        invoice = InvoiceModel(
            invoice_id=invoice_id or f"inv_{uuid4().hex}",
            tenant_id=tenant_id,
            uploaded_by_user_id=actor_user_id,
            customer_id=customer_id,
            file_name=file_name,
            storage_key=storage_key,
            status=InvoiceStatus.UPLOADED,
            payment_status=PaymentStatus.UNPAID,
            extracted_fields=extracted_fields,
            evidence_ids=[],
        )
        self.invoices.add(invoice)

        self.audit.record(
            tenant_id=tenant_id,
            action=AuditAction.INVOICE_UPLOADED,
            actor_user_id=actor_user_id,
            entity_type="invoice",
            entity_id=invoice.invoice_id,
            metadata={"file_name": file_name, "storage_key": storage_key},
        )

        self.session.commit()
        return invoice

    def list_invoices(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
    ) -> list[InvoiceModel]:
        actor = self.users.get(actor_user_id)

        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        if actor.tenant_id != tenant_id:
            raise PermissionError(f"User {actor_user_id} cannot access {tenant_id}.")

        return self.invoices.list_by_tenant(tenant_id)
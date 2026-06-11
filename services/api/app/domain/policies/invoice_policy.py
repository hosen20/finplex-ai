from app.domain.entities.invoice import Invoice
from app.domain.entities.tenant import Tenant
from app.domain.entities.user import User
from app.domain.enums import InvoiceStatus
from app.domain.exceptions import (
    CrossTenantAccessError,
    InvalidStateTransitionError,
    PermissionDeniedError,
)


class InvoicePolicy:
    """Business rules for invoice access and processing."""

    @staticmethod
    def ensure_can_upload(actor: User, tenant: Tenant) -> None:
        tenant.require_active()

        if actor.tenant_id != tenant.tenant_id:
            raise CrossTenantAccessError(
                f"User {actor.user_id} cannot upload to tenant {tenant.tenant_id}."
            )

        if not actor.is_active:
            raise PermissionDeniedError(f"User {actor.user_id} is inactive.")

    @staticmethod
    def ensure_can_view(actor: User, invoice: Invoice) -> None:
        if actor.tenant_id != invoice.tenant_id:
            raise CrossTenantAccessError(
                f"User {actor.user_id} cannot view invoice {invoice.invoice_id}."
            )

    @staticmethod
    def ensure_can_process(invoice: Invoice) -> None:
        if invoice.status not in {
            InvoiceStatus.UPLOADED,
            InvoiceStatus.PROCESSING,
            InvoiceStatus.EXTRACTED,
        }:
            message = (
                f"Invoice {invoice.invoice_id} cannot be processed "
                f"from {invoice.status}."
            )
            raise InvalidStateTransitionError(message)
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.enums import PaymentStatus


@dataclass(slots=True)
class ERPInvoiceRecord:
    erp_invoice_id: str
    tenant_id: str
    customer_id: str
    invoice_number: str
    amount_due: Decimal
    currency: str
    due_date: date
    payment_status: PaymentStatus
    total_paid: Decimal = Decimal("0.00")
    payment_terms_days: int = 30

    @property
    def outstanding_amount(self) -> Decimal:
        remaining = self.amount_due - self.total_paid
        return max(remaining, Decimal("0.00"))

    def days_overdue(self, as_of: date) -> int:
        if as_of <= self.due_date:
            return 0
        return (as_of - self.due_date).days

    def is_overdue(self, as_of: date) -> bool:
        return self.outstanding_amount > 0 and self.days_overdue(as_of) > 0


@dataclass(slots=True)
class ERPPaymentRecord:
    payment_id: str
    tenant_id: str
    customer_id: str
    erp_invoice_id: str
    amount: Decimal
    currency: str
    paid_at: date
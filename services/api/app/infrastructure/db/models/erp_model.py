from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import PaymentStatus
from app.infrastructure.db.models.base import Base, TimestampMixin


class ERPInvoiceModel(Base, TimestampMixin):
    __tablename__ = "erp_invoices"

    erp_invoice_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    customer_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(128), index=True)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False),
        nullable=False,
    )
    total_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    payment_terms_days: Mapped[int] = mapped_column(default=30)


class ERPPaymentModel(Base, TimestampMixin):
    __tablename__ = "erp_payments"

    payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    erp_invoice_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("erp_invoices.erp_invoice_id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    paid_at: Mapped[date] = mapped_column(Date, nullable=False)
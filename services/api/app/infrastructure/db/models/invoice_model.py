from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import InvoiceStatus, PaymentStatus
from app.infrastructure.db.models.base import Base, TimestampMixin


class InvoiceModel(Base, TimestampMixin):
    __tablename__ = "invoices"

    invoice_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    uploaded_by_user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("customers.customer_id", ondelete="SET NULL"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, native_enum=False),
        default=InvoiceStatus.UPLOADED,
        index=True,
        nullable=False,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False),
        default=PaymentStatus.UNPAID,
        nullable=False,
    )
    extracted_fields: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
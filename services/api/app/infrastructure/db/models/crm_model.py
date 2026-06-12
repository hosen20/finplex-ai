from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base, TimestampMixin


class CRMNoteModel(Base, TimestampMixin):
    __tablename__ = "crm_notes"

    note_id: Mapped[str] = mapped_column(String(64), primary_key=True)
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
    author_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class CRMDisputeModel(Base, TimestampMixin):
    __tablename__ = "crm_disputes"

    dispute_id: Mapped[str] = mapped_column(String(64), primary_key=True)
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
    invoice_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
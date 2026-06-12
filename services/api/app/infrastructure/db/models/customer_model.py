from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base, TimestampMixin


class CustomerModel(Base, TimestampMixin):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_contact_channel: Mapped[str] = mapped_column(
        String(64),
        default="email",
    )
    relationship_status: Mapped[str] = mapped_column(String(64), default="normal")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
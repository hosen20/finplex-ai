from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import ReviewStatus, RiskLevel
from app.infrastructure.db.models.base import Base, TimestampMixin


class ReviewModel(Base, TimestampMixin):
    __tablename__ = "reviews"

    review_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    invoice_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("invoices.invoice_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    draft_message: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, native_enum=False),
        nullable=False,
    )
    guardrails_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, native_enum=False),
        default=ReviewStatus.PENDING,
        index=True,
        nullable=False,
    )
    reviewer_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
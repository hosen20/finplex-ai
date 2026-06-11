from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from app.domain.enums import InvoiceStatus, PaymentStatus
from app.domain.exceptions import InvalidStateTransitionError


@dataclass(slots=True)
class InvoiceExtractedFields:
    invoice_number: str
    customer_name: str
    amount_due: Decimal
    currency: str
    issue_date: date | None = None
    due_date: date | None = None
    confidence: float = 0.0

    def is_confident(self, threshold: float = 0.75) -> bool:
        return self.confidence >= threshold


@dataclass(slots=True)
class Invoice:
    invoice_id: str
    tenant_id: str
    uploaded_by_user_id: str
    file_name: str
    storage_key: str
    customer_id: str | None = None
    status: InvoiceStatus = InvoiceStatus.UPLOADED
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    extracted_fields: InvoiceExtractedFields | None = None
    evidence_ids: list[str] = field(default_factory=list)
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime | None = None

    def mark_processing(self) -> None:
        if self.status != InvoiceStatus.UPLOADED:
            raise InvalidStateTransitionError(
                f"Cannot move invoice from {self.status} to processing."
            )
        self.status = InvoiceStatus.PROCESSING
        self.updated_at = datetime.now(UTC)

    def attach_extracted_fields(self, fields: InvoiceExtractedFields) -> None:
        if self.status not in {InvoiceStatus.UPLOADED, InvoiceStatus.PROCESSING}:
            raise InvalidStateTransitionError(
                f"Cannot attach extracted fields when status is {self.status}."
            )
        self.extracted_fields = fields
        self.status = InvoiceStatus.EXTRACTED
        self.updated_at = datetime.now(UTC)

    def mark_review_pending(self) -> None:
        if self.status not in {
            InvoiceStatus.EXTRACTED,
            InvoiceStatus.SCORED,
            InvoiceStatus.DRAFTED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot move invoice from {self.status} to review pending."
            )
        self.status = InvoiceStatus.REVIEW_PENDING
        self.updated_at = datetime.now(UTC)

    def add_evidence(self, evidence_id: str) -> None:
        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(evidence_id)
            self.updated_at = datetime.now(UTC)
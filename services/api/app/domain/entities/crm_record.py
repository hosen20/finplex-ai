from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class CRMNote:
    note_id: str
    tenant_id: str
    customer_id: str
    author_user_id: str
    body: str
    created_at: datetime = datetime.now(UTC)


@dataclass(slots=True)
class CRMDispute:
    dispute_id: str
    tenant_id: str
    customer_id: str
    invoice_number: str | None
    reason: str
    is_open: bool = True
    created_at: datetime = datetime.now(UTC)


@dataclass(slots=True)
class CRMContext:
    tenant_id: str
    customer_id: str
    notes: list[CRMNote] = field(default_factory=list)
    disputes: list[CRMDispute] = field(default_factory=list)
    promise_to_pay_date: datetime | None = None

    @property
    def has_open_dispute(self) -> bool:
        return any(dispute.is_open for dispute in self.disputes)

    @property
    def latest_note(self) -> CRMNote | None:
        if not self.notes:
            return None
        return max(self.notes, key=lambda note: note.created_at)
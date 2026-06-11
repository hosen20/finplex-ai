from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.enums import ReviewStatus, RiskLevel
from app.domain.exceptions import InvalidStateTransitionError, MissingEvidenceError


@dataclass(slots=True)
class Review:
    review_id: str
    tenant_id: str
    invoice_id: str
    draft_message: str
    risk_level: RiskLevel
    guardrails_passed: bool
    evidence_ids: list[str] = field(default_factory=list)
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_user_id: str | None = None
    reviewer_comment: str | None = None
    created_at: datetime = datetime.now(UTC)
    decided_at: datetime | None = None

    def require_pending(self) -> None:
        if self.status != ReviewStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Review {self.review_id} is already {self.status}."
            )

    def require_evidence(self) -> None:
        if not self.evidence_ids:
            raise MissingEvidenceError(
                f"Review {self.review_id} cannot be decided without evidence."
            )

    def approve(self, reviewer_user_id: str, comment: str | None = None) -> None:
        self.require_pending()
        self.require_evidence()

        if not self.guardrails_passed:
            raise InvalidStateTransitionError(
                "Cannot approve a draft that failed guardrails."
            )

        self.status = ReviewStatus.APPROVED
        self.reviewer_user_id = reviewer_user_id
        self.reviewer_comment = comment
        self.decided_at = datetime.now(UTC)

    def reject(self, reviewer_user_id: str, comment: str) -> None:
        self.require_pending()
        self.status = ReviewStatus.REJECTED
        self.reviewer_user_id = reviewer_user_id
        self.reviewer_comment = comment
        self.decided_at = datetime.now(UTC)

    def request_changes(self, reviewer_user_id: str, comment: str) -> None:
        self.require_pending()
        self.status = ReviewStatus.NEEDS_CHANGES
        self.reviewer_user_id = reviewer_user_id
        self.reviewer_comment = comment
        self.decided_at = datetime.now(UTC)
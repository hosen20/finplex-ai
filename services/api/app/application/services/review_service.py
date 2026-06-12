from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.application.services.mappers import (
    review_model_to_domain,
    user_model_to_domain,
)
from app.domain.enums import AuditAction, ReviewStatus, RiskLevel
from app.domain.policies.review_policy import ReviewPolicy
from app.infrastructure.db.models.review_model import ReviewModel
from app.infrastructure.db.repositories.invoice_repository import InvoiceRepository
from app.infrastructure.db.repositories.review_repository import ReviewRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


class ReviewService:
    """Application workflows for human review decisions."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.reviews = ReviewRepository(session)
        self.invoices = InvoiceRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def create_review(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        draft_message: str,
        risk_level: RiskLevel,
        guardrails_passed: bool,
        evidence_ids: list[str],
    ) -> ReviewModel:
        invoice = self.invoices.get(invoice_id)

        if invoice is None:
            raise ValueError(f"Invoice {invoice_id} was not found.")
        if invoice.tenant_id != tenant_id:
            raise PermissionError(f"Invoice {invoice_id} is not in tenant {tenant_id}.")

        review = ReviewModel(
            review_id=f"review_{uuid4().hex}",
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            draft_message=draft_message,
            risk_level=risk_level,
            guardrails_passed=guardrails_passed,
            evidence_ids=evidence_ids,
            status=ReviewStatus.PENDING,
        )
        self.reviews.add(review)

        self.audit.record(
            tenant_id=tenant_id,
            action=AuditAction.DRAFT_CREATED,
            actor_user_id=None,
            entity_type="review",
            entity_id=review.review_id,
            metadata={"invoice_id": invoice_id, "risk_level": risk_level.value},
        )

        self.session.commit()
        return review

    def list_pending_reviews(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
    ) -> list[ReviewModel]:
        actor = self._get_actor(actor_user_id)
        if actor.tenant_id != tenant_id:
            raise PermissionError(f"User {actor_user_id} cannot access {tenant_id}.")

        return self.reviews.list_pending_by_tenant(tenant_id)

    def approve_review(
        self,
        *,
        review_id: str,
        actor_user_id: str,
        comment: str | None = None,
    ) -> ReviewModel:
        review = self._get_review(review_id)
        actor = self._get_actor(actor_user_id)

        ReviewPolicy.ensure_can_review(
            user_model_to_domain(actor),
            review_model_to_domain(review),
        )

        domain_review = review_model_to_domain(review)
        domain_review.approve(actor_user_id, comment)

        review.status = domain_review.status
        review.reviewer_user_id = actor_user_id
        review.reviewer_comment = comment

        self.audit.record(
            tenant_id=review.tenant_id,
            action=AuditAction.DRAFT_APPROVED,
            actor_user_id=actor_user_id,
            entity_type="review",
            entity_id=review.review_id,
        )

        self.session.commit()
        return review

    def reject_review(
        self,
        *,
        review_id: str,
        actor_user_id: str,
        comment: str,
    ) -> ReviewModel:
        review = self._get_review(review_id)
        actor = self._get_actor(actor_user_id)

        ReviewPolicy.ensure_can_review(
            user_model_to_domain(actor),
            review_model_to_domain(review),
        )

        domain_review = review_model_to_domain(review)
        domain_review.reject(actor_user_id, comment)

        review.status = domain_review.status
        review.reviewer_user_id = actor_user_id
        review.reviewer_comment = comment

        self.audit.record(
            tenant_id=review.tenant_id,
            action=AuditAction.DRAFT_REJECTED,
            actor_user_id=actor_user_id,
            entity_type="review",
            entity_id=review.review_id,
            metadata={"comment": comment},
        )

        self.session.commit()
        return review

    def request_changes(
        self,
        *,
        review_id: str,
        actor_user_id: str,
        comment: str,
    ) -> ReviewModel:
        review = self._get_review(review_id)
        actor = self._get_actor(actor_user_id)

        ReviewPolicy.ensure_can_review(
            user_model_to_domain(actor),
            review_model_to_domain(review),
        )

        domain_review = review_model_to_domain(review)
        domain_review.request_changes(actor_user_id, comment)

        review.status = domain_review.status
        review.reviewer_user_id = actor_user_id
        review.reviewer_comment = comment

        self.session.commit()
        return review

    def _get_review(self, review_id: str) -> ReviewModel:
        review = self.reviews.get(review_id)
        if review is None:
            raise ValueError(f"Review {review_id} was not found.")
        return review

    def _get_actor(self, actor_user_id: str):
        actor = self.users.get(actor_user_id)
        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")
        return actor
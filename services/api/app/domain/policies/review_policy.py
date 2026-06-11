from app.domain.entities.review import Review
from app.domain.entities.user import User
from app.domain.exceptions import CrossTenantAccessError, PermissionDeniedError


class ReviewPolicy:
    """Business rules for human review decisions."""

    @staticmethod
    def ensure_can_review(actor: User, review: Review) -> None:
        if actor.tenant_id != review.tenant_id:
            raise CrossTenantAccessError(
                f"User {actor.user_id} cannot review tenant {review.tenant_id}."
            )

        if not actor.is_active:
            raise PermissionDeniedError(f"User {actor.user_id} is inactive.")

        if not actor.can_review_drafts:
            raise PermissionDeniedError(
                f"User {actor.user_id} cannot approve or reject drafts."
            )

    @staticmethod
    def ensure_can_view_review(actor: User, review: Review) -> None:
        if actor.tenant_id != review.tenant_id:
            raise CrossTenantAccessError(
                f"User {actor.user_id} cannot view review {review.review_id}."
            )
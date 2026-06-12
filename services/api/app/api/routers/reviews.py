from app.api.schemas.review import (
    ReviewCreateRequest,
    ReviewDecisionRequest,
    ReviewRejectRequest,
    ReviewResponse,
)
from app.application.services.review_service import ReviewService
from app.database import get_db_session
from app.dependencies import get_current_user
from app.domain.exceptions import CrossTenantAccessError
from app.infrastructure.db.models.user_model import UserModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
def create_review(
    payload: ReviewCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    if current_user.tenant_id != payload.tenant_id:
        raise CrossTenantAccessError(
            f"User {current_user.user_id} cannot create reviews "
            f"for tenant {payload.tenant_id}."
        )

    service = ReviewService(session)
    return service.create_review(
        tenant_id=payload.tenant_id,
        invoice_id=payload.invoice_id,
        draft_message=payload.draft_message,
        risk_level=payload.risk_level,
        guardrails_passed=payload.guardrails_passed,
        evidence_ids=payload.evidence_ids,
    )


@router.get("/pending", response_model=list[ReviewResponse])
def list_pending_reviews(
    tenant_id: str = Query(...),
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = ReviewService(session)
    return service.list_pending_reviews(
        tenant_id=tenant_id,
        actor_user_id=current_user.user_id,
    )


@router.post("/{review_id}/approve", response_model=ReviewResponse)
def approve_review(
    review_id: str,
    payload: ReviewDecisionRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = ReviewService(session)
    return service.approve_review(
        review_id=review_id,
        actor_user_id=current_user.user_id,
        comment=payload.comment,
    )


@router.post("/{review_id}/reject", response_model=ReviewResponse)
def reject_review(
    review_id: str,
    payload: ReviewRejectRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = ReviewService(session)
    return service.reject_review(
        review_id=review_id,
        actor_user_id=current_user.user_id,
        comment=payload.comment,
    )


@router.post("/{review_id}/request-changes", response_model=ReviewResponse)
def request_changes(
    review_id: str,
    payload: ReviewRejectRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = ReviewService(session)
    return service.request_changes(
        review_id=review_id,
        actor_user_id=current_user.user_id,
        comment=payload.comment,
    )
from datetime import datetime

from app.domain.enums import ReviewStatus, RiskLevel
from pydantic import BaseModel, ConfigDict


class ReviewCreateRequest(BaseModel):
    tenant_id: str | None = None
    invoice_id: str
    draft_message: str
    risk_level: RiskLevel
    guardrails_passed: bool
    evidence_ids: list[str]


class ReviewDecisionRequest(BaseModel):
    comment: str | None = None


class ReviewRejectRequest(BaseModel):
    comment: str


class ReviewResponse(BaseModel):
    review_id: str
    tenant_id: str
    invoice_id: str
    draft_message: str
    risk_level: RiskLevel
    guardrails_passed: bool
    evidence_ids: list[str]
    status: ReviewStatus
    reviewer_user_id: str | None = None
    reviewer_comment: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error"]


class GuardrailFinding(BaseModel):
    """One policy finding produced by the guardrails service."""

    code: str
    severity: Severity
    message: str
    policy_reference: str
    matched_text: str | None = None


class MessageValidationRequest(BaseModel):
    """Request body for validating an AI-generated collection draft."""

    tenant_id: str
    invoice_id: str
    draft_message: str = Field(min_length=1)
    risk_level: str = "medium"
    evidence_ids: list[str] = Field(default_factory=list)
    customer_name: str | None = None
    amount_due: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageValidationResponse(BaseModel):
    """Guardrail result returned before a draft is placed in review."""

    tenant_id: str
    invoice_id: str
    passed: bool
    decision: str
    findings: list[GuardrailFinding] = Field(default_factory=list)
    redacted_message: str
    evidence_ids: list[str] = Field(default_factory=list)
    policy_version: str
    human_review_required: bool = True
    nemo_passed: bool
    nemo_messages: list[str] = Field(default_factory=list)
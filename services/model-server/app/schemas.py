from typing import Any, Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]


class InvoiceExtractionRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    file_name: str
    storage_key: str
    text: str | None = None


class ExtractedInvoiceFields(BaseModel):
    invoice_number: str | None = None
    customer_name: str | None = None
    amount_due: float | None = Field(default=None, ge=0)
    currency: str = "USD"
    due_date: str | None = None
    payment_terms: str | None = None


class InvoiceExtractionResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    extracted_fields: ExtractedInvoiceFields
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]
    model_version: str


class RiskScoreRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    days_overdue: int = Field(default=0, ge=0)
    has_dispute: bool = False
    previous_late_payments: int = Field(default=0, ge=0)
    customer_relationship_status: str = "normal"


class RiskScoreResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0, le=1)
    reasons: list[str]
    model_version: str


class DraftMessageRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    customer_name: str = "Customer"
    contact_name: str | None = None
    invoice_number: str | None = None
    amount_due: float | None = Field(default=None, ge=0)
    currency: str = "USD"
    due_date: str | None = None
    risk_level: RiskLevel = "low"
    evidence_ids: list[str] = Field(default_factory=list)


class DraftMessageResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    draft_message: str
    guardrails_required: bool
    evidence_ids: list[str]
    model_version: str


class InvoicePipelineRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    file_name: str
    storage_key: str
    text: str | None = None
    days_overdue: int = Field(default=0, ge=0)
    has_dispute: bool = False
    previous_late_payments: int = Field(default=0, ge=0)
    customer_relationship_status: str = "normal"


class InvoicePipelineResponse(BaseModel):
    extraction: InvoiceExtractionResponse
    risk: RiskScoreResponse
    draft: DraftMessageResponse
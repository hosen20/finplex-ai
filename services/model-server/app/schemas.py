from typing import Any

from pydantic import BaseModel, Field


class ExtractedInvoiceFields(BaseModel):
    invoice_number: str | None = None
    customer_name: str | None = None
    amount_due: float | None = None
    currency: str = "USD"
    due_date: str | None = None
    payment_terms: str | None = None


class InvoiceExtractionRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    file_name: str | None = None
    storage_key: str | None = None
    text: str | None = None


class InvoiceExtractionResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    extracted_fields: ExtractedInvoiceFields
    confidence: float = Field(..., ge=0, le=1)
    evidence_ids: list[str] = Field(default_factory=list)
    model_version: str


class RiskFeaturePayload(BaseModel):
    amount_due: float = Field(..., ge=0)
    payment_terms_days: int = Field(..., ge=0)
    paperless_bill: int = Field(0, ge=0, le=1)
    country_code: str = "UNKNOWN"

    previous_invoice_count: int = Field(..., ge=0)
    previous_late_payments: int = Field(..., ge=0)
    previous_disputed_count: int = Field(..., ge=0)
    previous_total_amount: float = Field(..., ge=0)
    previous_average_invoice_amount: float = Field(..., ge=0)
    previous_average_days_late: float = Field(..., ge=0)
    previous_max_days_late: float = Field(..., ge=0)
    previous_on_time_payment_rate: float = Field(..., ge=0, le=1)
    previous_dispute_rate: float = Field(..., ge=0, le=1)
    previous_crm_negative_signal_score: float = Field(..., ge=0, le=1)
    relationship_age_days: int = Field(..., ge=0)


class RiskSignal(BaseModel):
    name: str
    value: float | int | str
    reason: str


class RiskScoreRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    days_overdue: int = Field(0, ge=0)
    has_dispute: bool = False
    previous_late_payments: int = Field(0, ge=0)
    customer_relationship_status: str = "active"
    risk_features: RiskFeaturePayload | None = None


class RiskScoreResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    risk_level: str
    risk_score: float = Field(..., ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    model_version: str

    model_loaded: bool = False
    model_name: str = "deterministic_fallback"
    probabilities: dict[str, float] = Field(default_factory=dict)
    feature_source: str = "deterministic_fallback"
    top_risk_signals: list[RiskSignal] = Field(default_factory=list)


class DraftMessageRequest(BaseModel):
    invoice_id: str
    tenant_id: str
    customer_name: str
    invoice_number: str | None = None
    contact_name: str | None = None
    amount_due: float | None = None
    currency: str = "USD"
    due_date: str | None = None
    risk_level: str
    evidence_ids: list[str] = Field(default_factory=list)


class DraftMessageResponse(BaseModel):
    invoice_id: str
    tenant_id: str
    draft_message: str
    guardrails_required: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    model_version: str


class InvoicePipelineRequest(InvoiceExtractionRequest):
    days_overdue: int = Field(0, ge=0)
    has_dispute: bool = False
    previous_late_payments: int = Field(0, ge=0)
    customer_relationship_status: str = "active"
    risk_features: RiskFeaturePayload | None = None


class InvoicePipelineResponse(BaseModel):
    extraction: InvoiceExtractionResponse
    risk: RiskScoreResponse
    draft: DraftMessageResponse
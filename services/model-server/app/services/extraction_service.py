import re

from app.config import settings
from app.schemas import (
    ExtractedInvoiceFields,
    InvoiceExtractionRequest,
    InvoiceExtractionResponse,
)

_AMOUNT_PATTERN = re.compile(
    r"(?:amount due|total|balance)[:\s$]*"
    r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
    re.IGNORECASE,
)

_CUSTOMER_PATTERN = re.compile(
    r"(?:customer|bill to)[:\s]+"
    r"(.+?)"
    r"(?=\s+(?:amount due|total|balance|due date|payment due|"
    r"invoice number|invoice no|invoice #|inv)\b|$)",
    re.IGNORECASE,
)

_DUE_DATE_PATTERN = re.compile(
    r"(?:due date|payment due)[:\s]+("
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}|"
    r"[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}"
    r")",
    re.IGNORECASE,
)

_INVOICE_NUMBER_PATTERN = re.compile(
    r"(?:invoice number|invoice no|invoice #|inv)[:#\s-]*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)


class InvoiceExtractionService:
    """Deterministic placeholder extractor for invoice fields."""

    def extract(self, request: InvoiceExtractionRequest) -> InvoiceExtractionResponse:
        text = request.text or ""
        fields = ExtractedInvoiceFields(
            invoice_number=self._match_text(_INVOICE_NUMBER_PATTERN, text),
            customer_name=self._match_text(_CUSTOMER_PATTERN, text),
            amount_due=self._match_amount(text),
            due_date=self._match_text(_DUE_DATE_PATTERN, text),
            payment_terms="net_30" if "net 30" in text.lower() else None,
        )

        found_count = sum(
            value is not None
            for value in [
                fields.invoice_number,
                fields.customer_name,
                fields.amount_due,
                fields.due_date,
            ]
        )
        confidence = 0.35 + (found_count * 0.15)

        return InvoiceExtractionResponse(
            invoice_id=request.invoice_id,
            tenant_id=request.tenant_id,
            extracted_fields=fields,
            confidence=min(confidence, 0.95),
            evidence_ids=[f"ev_{request.invoice_id}_extraction"],
            model_version=settings.pipeline_version,
        )

    def _match_text(self, pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        if match is None:
            return None
        return match.group(1).strip().rstrip(".")

    def _match_amount(self, text: str) -> float | None:
        match = _AMOUNT_PATTERN.search(text)
        if match is None:
            return None
        return float(match.group(1).replace(",", ""))
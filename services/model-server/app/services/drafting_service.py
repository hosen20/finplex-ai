from app.config import settings
from app.schemas import DraftMessageRequest, DraftMessageResponse


class DraftingService:
    """Deterministic placeholder follow-up draft generator."""

    def create_draft(self, request: DraftMessageRequest) -> DraftMessageResponse:
        recipient = request.contact_name or request.customer_name
        invoice_label = request.invoice_number or request.invoice_id
        amount_text = ""
        if request.amount_due is not None:
            amount_text = f" for {request.currency} {request.amount_due:,.2f}"

        due_text = ""
        if request.due_date:
            due_text = f" due on {request.due_date}"

        tone_sentence = self._tone_sentence(request.risk_level)
        draft = (
            f"Hello {recipient},\n\n"
            f"I hope you are well. We are following up on invoice {invoice_label}"
            f"{amount_text}{due_text}. {tone_sentence}\n\n"
            "Please let us know if payment has already been arranged or if there "
            "is anything we should review with your team.\n\n"
            "Thank you."
        )

        return DraftMessageResponse(
            invoice_id=request.invoice_id,
            tenant_id=request.tenant_id,
            draft_message=draft,
            guardrails_required=True,
            evidence_ids=request.evidence_ids,
            model_version=settings.pipeline_version,
        )

    def _tone_sentence(self, risk_level: str) -> str:
        if risk_level in {"high", "critical"}:
            return (
                "We would appreciate a short update so we can resolve this "
                "responsibly."
            )
        if risk_level == "medium":
            return "Could you please share the expected payment timing?"
        return "This is a friendly reminder for your records."
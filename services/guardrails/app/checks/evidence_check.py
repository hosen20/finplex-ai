from typing import Any

from app.schemas import GuardrailFinding, MessageValidationRequest


class EvidenceCheck:
    """Ensures generated drafts are grounded in invoice/risk evidence."""

    def __init__(self, policies: dict[str, Any]) -> None:
        self.policies = policies

    def run(self, request: MessageValidationRequest) -> list[GuardrailFinding]:
        findings: list[GuardrailFinding] = []
        minimum = int(self.policies.get("required_evidence_minimum", 1))

        if len(request.evidence_ids) < minimum:
            findings.append(
                GuardrailFinding(
                    code="missing_evidence",
                    severity="error",
                    message="Draft requires at least one evidence reference.",
                    policy_reference="ai_governance/evidence_required_policy.md",
                )
            )

        if request.amount_due is not None and request.amount_due > 0:
            if not self._amount_appears_in_message(
                amount_due=request.amount_due,
                message=request.draft_message,
            ):
                findings.append(
                    GuardrailFinding(
                        code="amount_not_supported_in_message",
                        severity="warning",
                        message=(
                            "Amount due exists but is not clearly reflected "
                            "in the draft."
                        ),
                        policy_reference=(
                            "ai_governance/evidence_required_policy.md"
                        ),
                    )
                )

        return findings

    def _amount_appears_in_message(
        self,
        *,
        amount_due: float,
        message: str,
    ) -> bool:
        normalized_message = message.replace(",", "")
        amount_as_int = str(int(amount_due))
        amount_as_float = f"{amount_due:.2f}"

        return (
            amount_as_int in normalized_message
            or amount_as_float in normalized_message
        )
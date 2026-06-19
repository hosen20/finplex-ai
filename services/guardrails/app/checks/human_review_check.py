from app.schemas import GuardrailFinding, MessageValidationRequest


class HumanReviewCheck:
    """Marks every collection draft as requiring human approval."""

    def run(self, request: MessageValidationRequest) -> list[GuardrailFinding]:
        return [
            GuardrailFinding(
                code="human_review_required",
                severity="info",
                message="Draft must be reviewed by a human before sending.",
                policy_reference="debt_collection/human_approval_policy.md",
            )
        ]
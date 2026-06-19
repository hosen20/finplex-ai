from app.schemas import GuardrailFinding, MessageValidationRequest
from app.utils.redaction import contains_sensitive_identifier


class PrivacyCheck:
    """Blocks drafts that expose sensitive identifiers."""

    def run(self, request: MessageValidationRequest) -> list[GuardrailFinding]:
        if not contains_sensitive_identifier(request.draft_message):
            return []

        return [
            GuardrailFinding(
                code="sensitive_identifier_exposed",
                severity="error",
                message="Draft exposes sensitive identifiers and must be rewritten.",
                policy_reference="privacy_security/pii_redaction_policy.md",
            )
        ]
import re
from typing import Any

from app.schemas import GuardrailFinding, MessageValidationRequest


class ProhibitedLanguageCheck:
    """Blocks legal threats, harassment, and false consequence language."""

    def __init__(self, policies: dict[str, Any]) -> None:
        self.policies = policies

    def run(self, request: MessageValidationRequest) -> list[GuardrailFinding]:
        findings: list[GuardrailFinding] = []
        message_lower = request.draft_message.lower()

        for phrase in self.policies.get("prohibited_phrases", []):
            phrase_text = str(phrase).lower()
            if phrase_text in message_lower:
                findings.append(
                    GuardrailFinding(
                        code="prohibited_language",
                        severity="error",
                        message=(
                            "Draft contains prohibited debt-collection "
                            "language."
                        ),
                        policy_reference="debt_collection/prohibited_claims.md",
                        matched_text=str(phrase),
                    )
                )

        for pattern in self.policies.get("prohibited_regex", []):
            match = re.search(str(pattern), request.draft_message, re.IGNORECASE)
            if match is not None:
                findings.append(
                    GuardrailFinding(
                        code="prohibited_pattern",
                        severity="error",
                        message=(
                            "Draft contains a prohibited threat, legal claim, "
                            "or intimidation pattern."
                        ),
                        policy_reference="debt_collection/fdcpa_alignment.md",
                        matched_text=match.group(0),
                    )
                )

        return findings
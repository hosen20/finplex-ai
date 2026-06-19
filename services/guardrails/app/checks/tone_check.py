from typing import Any

from app.schemas import GuardrailFinding, MessageValidationRequest


class ToneCheck:
    """Warns when the draft tone is too aggressive."""

    def __init__(self, policies: dict[str, Any]) -> None:
        self.policies = policies

    def run(self, request: MessageValidationRequest) -> list[GuardrailFinding]:
        findings: list[GuardrailFinding] = []
        message = request.draft_message
        message_lower = message.lower()
        words = [word for word in message.split() if word.isalpha()]

        uppercase_ratio = self._uppercase_ratio(words)
        max_uppercase_ratio = float(
            self.policies.get("max_uppercase_ratio", 0.35)
        )
        if uppercase_ratio > max_uppercase_ratio:
            findings.append(
                GuardrailFinding(
                    code="aggressive_tone_uppercase",
                    severity="warning",
                    message="Draft uses too much uppercase text.",
                    policy_reference="debt_collection/prohibited_tone.md",
                )
            )

        max_exclamation_marks = int(
            self.policies.get("max_exclamation_marks", 1)
        )
        if message.count("!") > max_exclamation_marks:
            findings.append(
                GuardrailFinding(
                    code="aggressive_tone_punctuation",
                    severity="warning",
                    message="Draft uses excessive exclamation marks.",
                    policy_reference="debt_collection/prohibited_tone.md",
                )
            )

        for term in self.policies.get("aggressive_terms", []):
            term_text = str(term).lower()
            if term_text in message_lower:
                findings.append(
                    GuardrailFinding(
                        code="aggressive_tone_term",
                        severity="warning",
                        message=(
                            "Draft contains wording that may sound aggressive."
                        ),
                        policy_reference="debt_collection/prohibited_tone.md",
                        matched_text=str(term),
                    )
                )

        return findings

    def _uppercase_ratio(self, words: list[str]) -> float:
        if not words:
            return 0.0

        uppercase_words = [word for word in words if word.isupper()]
        return len(uppercase_words) / len(words)
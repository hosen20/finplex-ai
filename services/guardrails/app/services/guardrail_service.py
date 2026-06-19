from app.checks import (
    EvidenceCheck,
    HumanReviewCheck,
    PrivacyCheck,
    ProhibitedLanguageCheck,
    ToneCheck,
)
from app.config import settings
from app.nemo_adapter import NemoGuardrailsAdapter
from app.policy_loader import PolicyLoader
from app.schemas import (
    GuardrailFinding,
    MessageValidationRequest,
    MessageValidationResponse,
)
from app.utils.redaction import redact_pii


class GuardrailService:
    """Validates draft messages before they are sent to human review."""

    def __init__(
        self,
        *,
        policy_loader: PolicyLoader | None = None,
        nemo_adapter: NemoGuardrailsAdapter | None = None,
    ) -> None:
        self.policy_loader = policy_loader or PolicyLoader()
        self.policies = self.policy_loader.load()
        self.nemo_adapter = nemo_adapter or NemoGuardrailsAdapter(
            config_dir=settings.nemo_config_dir
        )

        self.checks = [
            ProhibitedLanguageCheck(self.policies),
            ToneCheck(self.policies),
            EvidenceCheck(self.policies),
            PrivacyCheck(),
            HumanReviewCheck(),
        ]

    def validate(
        self,
        request: MessageValidationRequest,
    ) -> MessageValidationResponse:
        findings: list[GuardrailFinding] = []

        nemo_passed, nemo_messages = self.nemo_adapter.validate_output(
            request.draft_message
        )
        if not nemo_passed:
            findings.append(
                GuardrailFinding(
                    code="nemo_guardrails_blocked",
                    severity="error",
                    message="NeMo Guardrails blocked the draft.",
                    policy_reference="nemo_config/rails.co",
                    matched_text="; ".join(nemo_messages),
                )
            )

        for check in self.checks:
            findings.extend(check.run(request))

        has_error = any(finding.severity == "error" for finding in findings)
        passed = not has_error
        decision = "send_to_human_review" if passed else "block_rewrite"

        return MessageValidationResponse(
            tenant_id=request.tenant_id,
            invoice_id=request.invoice_id,
            passed=passed,
            decision=decision,
            findings=findings,
            redacted_message=redact_pii(request.draft_message),
            evidence_ids=request.evidence_ids,
            policy_version=str(
                self.policies.get("policy_version", settings.policy_version)
            ),
            human_review_required=True,
            nemo_passed=nemo_passed,
            nemo_messages=nemo_messages,
        )
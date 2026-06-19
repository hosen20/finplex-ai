from typing import Any

from app.schemas import MessageValidationRequest
from app.services.guardrail_service import GuardrailService


class FakePolicyLoader:
    def load(self) -> dict[str, Any]:
        return {
            "policy_version": "test_policy_v1",
            "prohibited_phrases": [
                "we will sue you",
                "you will be arrested",
                "pay immediately or else",
            ],
            "prohibited_regex": [
                r"\bjail\b",
                r"\bcriminal\b",
            ],
            "aggressive_terms": [
                "harass",
                "blacklist",
            ],
            "required_evidence_minimum": 1,
            "max_exclamation_marks": 1,
            "max_uppercase_ratio": 0.35,
        }


class PassingFakeNemoAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def validate_output(self, message: str) -> tuple[bool, list[str]]:
        self.calls.append(message)
        return True, ["NeMo first-pass validation passed."]


class BlockingFakeNemoAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def validate_output(self, message: str) -> tuple[bool, list[str]]:
        self.calls.append(message)
        return False, ["NeMo Guardrails blocked unsafe collection language."]


def make_service(nemo_adapter) -> GuardrailService:
    return GuardrailService(
        policy_loader=FakePolicyLoader(),
        nemo_adapter=nemo_adapter,
    )


def make_request(
    *,
    draft_message: str,
    evidence_ids: list[str] | None = None,
    amount_due: float | None = 1200.0,
) -> MessageValidationRequest:
    if evidence_ids is None:
        evidence_ids = ["ev_invoice"]

    return MessageValidationRequest(
        tenant_id="tenant_1",
        invoice_id="inv_1",
        draft_message=draft_message,
        risk_level="medium",
        evidence_ids=evidence_ids,
        customer_name="Acme",
        amount_due=amount_due,
    )


def test_safe_message_passes_to_human_review() -> None:
    nemo = PassingFakeNemoAdapter()
    service = make_service(nemo)

    response = service.validate(
        make_request(
            draft_message=(
                "Hello Acme, our records show invoice INV-1 has an "
                "outstanding amount of 1200. Please let us know if you "
                "need any support."
            )
        )
    )

    assert response.passed is True
    assert response.decision == "send_to_human_review"
    assert response.human_review_required is True
    assert response.nemo_passed is True
    assert nemo.calls


def test_nemo_block_runs_before_deterministic_checks() -> None:
    nemo = BlockingFakeNemoAdapter()
    service = make_service(nemo)

    response = service.validate(
        make_request(
            draft_message="Hello, please review invoice INV-1 for 1200."
        )
    )

    assert response.passed is False
    assert response.decision == "block_rewrite"
    assert response.nemo_passed is False
    assert response.findings[0].code == "nemo_guardrails_blocked"
    assert nemo.calls


def test_deterministic_check_blocks_prohibited_language() -> None:
    service = make_service(PassingFakeNemoAdapter())

    response = service.validate(
        make_request(
            draft_message=(
                "Pay immediately or else. We will sue you for invoice INV-1."
            )
        )
    )

    codes = {finding.code for finding in response.findings}

    assert response.passed is False
    assert "prohibited_language" in codes


def test_missing_evidence_blocks_message() -> None:
    service = make_service(PassingFakeNemoAdapter())

    response = service.validate(
        make_request(
            draft_message="Please review invoice INV-1 for 1200.",
            evidence_ids=[],
        )
    )

    codes = {finding.code for finding in response.findings}

    assert response.passed is False
    assert "missing_evidence" in codes


def test_sensitive_identifier_is_redacted_and_blocked() -> None:
    service = make_service(PassingFakeNemoAdapter())

    response = service.validate(
        make_request(
            draft_message=(
                "Please pay invoice INV-1 for 1200. "
                "Customer SSN is 123-45-6789."
            )
        )
    )

    codes = {finding.code for finding in response.findings}

    assert response.passed is False
    assert "sensitive_identifier_exposed" in codes
    assert "123-45-6789" not in response.redacted_message
    assert "[REDACTED_ID]" in response.redacted_message
"""Run deterministic guardrails policy golden evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evals.common import EvalResult, exit_for_result, load_json, load_thresholds

GOLDEN_PATH = Path("data/golden/policy_cases.json")
PROHIBITED_PHRASES = (
    "legal action without further notice",
    "report you",
    "pay this invoice today or",
    "must pay the balance today",
)


def is_allowed(case: dict[str, Any]) -> bool:
    """Apply deterministic policy checks that mirror product guardrail intent."""
    draft_message = case["draft_message"].casefold()
    has_evidence = bool(case["evidence_ids"])
    requires_human_review = bool(case["human_review_required"])
    has_prohibited_phrase = any(
        phrase in draft_message for phrase in PROHIBITED_PHRASES
    )

    return has_evidence and requires_human_review and not has_prohibited_phrase


def evaluate() -> EvalResult:
    """Evaluate policy decision accuracy and unsafe block rate."""
    data = load_json(GOLDEN_PATH)
    thresholds = load_thresholds()
    cases: list[dict[str, Any]] = data["cases"]

    correct = 0
    unsafe_cases = 0
    unsafe_blocked = 0
    failures: list[str] = []

    for case in cases:
        predicted_allowed = is_allowed(case)
        expected_allowed = bool(case["expected_allowed"])
        if predicted_allowed == expected_allowed:
            correct += 1
        else:
            failures.append(
                
                    f"{case['case_id']}: expected allowed={expected_allowed}, "
                    f"got {predicted_allowed}"
                
            )

        if not expected_allowed:
            unsafe_cases += 1
            if not predicted_allowed:
                unsafe_blocked += 1

    decision_accuracy = correct / len(cases)
    unsafe_block_rate = unsafe_blocked / unsafe_cases
    accuracy_minimum = thresholds.get("policy_decision_accuracy_min", 0.95)
    block_minimum = thresholds.get("policy_unsafe_block_rate_min", 0.95)
    passed = (
        decision_accuracy >= accuracy_minimum
        and unsafe_block_rate >= block_minimum
    )

    return EvalResult(
        name="policy_eval",
        metrics={
            "decision_accuracy": decision_accuracy,
            "unsafe_block_rate": unsafe_block_rate,
        },
        passed=passed,
        failures=[] if passed else failures,
    )


if __name__ == "__main__":
    exit_for_result(evaluate())

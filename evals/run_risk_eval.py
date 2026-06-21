"""Run deterministic late-payment risk golden evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evals.common import EvalResult, exit_for_result, load_json, load_thresholds

GOLDEN_PATH = Path("data/golden/risk_expected.json")


def score_risk(features: dict[str, float]) -> str:
    """Classify risk using transparent product rules for CI regression checks."""
    days_overdue = features["days_overdue"]
    amount_due = features["amount_due"]
    late_payment_count = features["late_payment_count"]
    dispute_count = features["dispute_count"]
    recent_promises_to_pay = features["recent_promises_to_pay"]

    score = 0
    if days_overdue >= 45:
        score += 3
    elif days_overdue >= 15:
        score += 2
    elif days_overdue > 0:
        score += 1

    if amount_due >= 5000:
        score += 2
    elif amount_due >= 1000:
        score += 1

    if late_payment_count >= 3:
        score += 2
    elif late_payment_count >= 1:
        score += 1

    if dispute_count >= 2:
        score += 2
    elif dispute_count == 1:
        score += 1

    if recent_promises_to_pay > 0:
        score -= 1

    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def evaluate() -> EvalResult:
    """Evaluate deterministic risk-level agreement."""
    data = load_json(GOLDEN_PATH)
    thresholds = load_thresholds()
    cases: list[dict[str, Any]] = data["cases"]

    matches = 0
    failures: list[str] = []

    for case in cases:
        predicted = score_risk(case["features"])
        expected = case["expected_risk_level"]
        if predicted == expected:
            matches += 1
        else:
            failures.append(
                f"{case['case_id']}: expected {expected!r}, got {predicted!r}"
            )

    accuracy = matches / len(cases)
    minimum = thresholds.get("risk_level_accuracy_min", 0.8)

    return EvalResult(
        name="risk_eval",
        metrics={"risk_level_accuracy": accuracy},
        passed=accuracy >= minimum,
        failures=[] if accuracy >= minimum else failures,
    )


if __name__ == "__main__":
    exit_for_result(evaluate())

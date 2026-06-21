"""Run the offline end-to-end Finplex AI golden evaluation gate."""

from __future__ import annotations

from evals.common import EvalResult, exit_for_result, load_thresholds
from evals.run_extraction_eval import evaluate as evaluate_extraction
from evals.run_policy_eval import evaluate as evaluate_policy
from evals.run_rag_eval import evaluate as evaluate_rag
from evals.run_risk_eval import evaluate as evaluate_risk


def evaluate() -> EvalResult:
    """Pass only if every core AI evaluation gate passes."""
    thresholds = load_thresholds()
    child_results = [
        evaluate_extraction(),
        evaluate_rag(),
        evaluate_risk(),
        evaluate_policy(),
    ]

    passed_children = sum(1 for result in child_results if result.passed)
    success_rate = passed_children / len(child_results)
    minimum = thresholds.get("end_to_end_success_min", 1.0)
    failures = [
        f"{result.name} failed: {'; '.join(result.failures)}"
        for result in child_results
        if not result.passed
    ]

    return EvalResult(
        name="end_to_end_eval",
        metrics={"success_rate": success_rate},
        passed=success_rate >= minimum,
        failures=failures,
    )


if __name__ == "__main__":
    exit_for_result(evaluate())

from evals.run_end_to_end_eval import evaluate as evaluate_end_to_end
from evals.run_extraction_eval import evaluate as evaluate_extraction
from evals.run_policy_eval import evaluate as evaluate_policy
from evals.run_rag_eval import evaluate as evaluate_rag
from evals.run_risk_eval import evaluate as evaluate_risk


def test_extraction_eval_passes() -> None:
    assert evaluate_extraction().passed


def test_rag_eval_passes() -> None:
    assert evaluate_rag().passed


def test_risk_eval_passes() -> None:
    assert evaluate_risk().passed


def test_policy_eval_passes() -> None:
    assert evaluate_policy().passed


def test_end_to_end_eval_passes() -> None:
    assert evaluate_end_to_end().passed

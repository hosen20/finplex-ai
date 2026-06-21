# Evaluations

Evaluations protect the AI workflow from regressions. They are separate from normal unit tests because they check model behavior, retrieval quality, policy safety, and end-to-end product quality.

## Evaluation Types

| Eval | File | Purpose |
|---|---|---|
| Extraction eval | `evals/run_extraction_eval.py` | Checks invoice field extraction against expected fields |
| Risk eval | `evals/run_risk_eval.py` | Checks risk-level classification against expected levels |
| RAG eval | `evals/run_rag_eval.py` | Checks that retrieval returns the right evidence |
| Policy eval | `evals/run_policy_eval.py` | Checks that unsafe or unsupported drafts are blocked |
| End-to-end eval | `evals/run_end_to_end_eval.py` | Passes only when all core eval gates pass |

## Golden Data

Golden data lives in:

```text
data/golden/extraction_expected.json
data/golden/rag_questions.json
data/golden/policy_cases.json
data/golden/risk_expected.json
```

Each case is small, deterministic, and easy to inspect. This keeps the quality gate stable for CI while the larger OCR, pgvector, and LLM pipeline continues to improve.

## Thresholds

Thresholds live in:

```text
evals/eval_thresholds.yaml
```

Current categories:

```yaml
extraction_field_accuracy_min: 0.85
risk_level_accuracy_min: 0.80
rag_hit_at_3_min: 0.80
rag_required_term_coverage_min: 0.80
policy_decision_accuracy_min: 0.95
policy_unsafe_block_rate_min: 0.95
end_to_end_success_min: 1.00
```

Raise these thresholds as the product matures.

## Running Evals

Run all evals with:

```bash
bash scripts/run-evals.sh
```

Run individual evals with:

```bash
uv run --project services/api python -m evals.run_extraction_eval
uv run --project services/api python -m evals.run_rag_eval
uv run --project services/api python -m evals.run_risk_eval
uv run --project services/api python -m evals.run_policy_eval
uv run --project services/api python -m evals.run_end_to_end_eval
```

## Reports

Each eval writes a JSON report under:

```text
reports/evals/
```

These reports are local/generated artifacts and should not be committed.

## CI Quality Gate

The GitHub Actions workflow runs:

```bash
bash scripts/check-secrets.sh
bash scripts/lint.sh
bash scripts/test.sh
bash scripts/run-evals.sh
```

A pull request should not be merged if any of these fail.

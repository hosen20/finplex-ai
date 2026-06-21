# Evaluations

Evaluations protect the AI workflow from regressions. They are separate from normal unit tests because they check model behavior, retrieval quality, policy safety, and end-to-end product quality.

## Evaluation Types

| Eval | Purpose |
|---|---|
| Extraction eval | Checks invoice field extraction against expected fields |
| Risk eval | Checks risk model outputs against expected levels or score ranges |
| RAG eval | Checks that retrieval returns the right evidence |
| Policy eval | Checks that unsafe or unsupported drafts are blocked |
| End-to-end eval | Checks that an invoice can move from upload to human review |

## Golden Data

Golden data should live in:

```text
data/golden/extraction_expected.json
data/golden/rag_questions.json
data/golden/policy_cases.json
data/golden/risk_expected.json
```

Each case should be small, deterministic, and easy to inspect.

## Thresholds

Thresholds should live in:

```text
evals/eval_thresholds.yaml
```

Example threshold categories:

```yaml
extraction_field_accuracy_min: 0.80
rag_hit_at_3_min: 0.80
policy_block_rate_min: 0.95
risk_level_accuracy_min: 0.70
end_to_end_success_min: 1.00
```

## Running Evals

Once golden data is populated, evals should run with:

```bash
uv run --project services/model-server python evals/run_extraction_eval.py
uv run --project services/model-server python evals/run_risk_eval.py
uv run --project services/model-server python evals/run_rag_eval.py
uv run --project services/guardrails python evals/run_policy_eval.py
uv run --project services/api python evals/run_end_to_end_eval.py
```

A wrapper script can run all evals:

```bash
bash scripts/run-evals.sh
```

## What Makes An Eval Useful

A useful eval includes:

- a clear input
- an expected output or acceptance rule
- a scoring function
- a threshold
- a short failure message
- stable local data

## CI Quality Gate

The quality gate should eventually include:

1. Python linting
2. backend tests
3. model-server tests
4. guardrails tests
5. worker tests
6. React build
7. Streamlit import check
8. migration check
9. golden evals
10. secret scan

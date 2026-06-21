#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p reports/evals

echo "Running extraction eval..."
uv run --project services/api python -m evals.run_extraction_eval

echo "Running RAG eval..."
uv run --project services/api python -m evals.run_rag_eval

echo "Running risk eval..."
uv run --project services/api python -m evals.run_risk_eval

echo "Running policy eval..."
uv run --project services/api python -m evals.run_policy_eval

echo "Running end-to-end eval gate..."
uv run --project services/api python -m evals.run_end_to_end_eval

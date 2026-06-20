#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

echo "Running Finplex AI demo smoke flow..."
uv run --project services/api python3 scripts/run_demo_flow.py

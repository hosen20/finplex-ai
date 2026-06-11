#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

cd "${ROOT_DIR}/services/guardrails"

uv run uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port "${GUARDRAILS_PORT:-8002}"
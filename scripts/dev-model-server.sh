#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

cd "${ROOT_DIR}/services/model-server"

uv run uvicorn app.main:app \
  --reload \
  --host 0.0.0.0 \
  --port "${MODEL_SERVER_PORT:-8001}"
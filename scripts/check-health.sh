#!/usr/bin/env bash
set -euo pipefail

check_url() {
  local name="$1"
  local url="$2"

  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "${name}: ok"
  else
    echo "${name}: not reachable at ${url}" >&2
    return 1
  fi
}

check_url "API" "http://localhost:8000/health"
check_url "model-server" "http://localhost:8001/health"
check_url "guardrails" "http://localhost:8002/health"
check_url "dashboard" "http://localhost:5173"

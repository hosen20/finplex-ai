#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
MODEL_SERVER_URL="${MODEL_SERVER_URL:-http://localhost:8001}"
GUARDRAILS_URL="${GUARDRAILS_URL:-http://localhost:8002}"
WEB_URL="${WEB_URL:-http://localhost:5173}"

print_ok() {
  printf "✅ %s\n" "$1"
}

print_fail() {
  printf "❌ %s\n" "$1"
}

check_json_health() {
  local name="$1"
  local url="$2"

  if curl -fsS --max-time 3 "${url}/health" >/tmp/finplex-health.json 2>/dev/null; then
    print_ok "${name} is healthy at ${url}"
  else
    print_fail "${name} is not reachable at ${url}"
    return 1
  fi
}

check_web() {
  if curl -fsS --max-time 3 "${WEB_URL}" >/dev/null 2>/dev/null; then
    print_ok "Dashboard is reachable at ${WEB_URL}"
  else
    print_fail "Dashboard is not reachable at ${WEB_URL}"
    return 1
  fi
}

main() {
  local failed=0

  echo "Checking Finplex AI local demo services..."
  echo

  check_json_health "API" "${API_URL}" || failed=1
  check_json_health "model-server" "${MODEL_SERVER_URL}" || failed=1
  check_json_health "guardrails" "${GUARDRAILS_URL}" || failed=1
  check_web || failed=1

  echo
  if [[ "${failed}" -eq 0 ]]; then
    print_ok "All demo services are reachable."
  else
    print_fail "One or more demo services are not running. Open the runbook: docs/DEMO_RUNBOOK.md"
    exit 1
  fi
}

main "$@"

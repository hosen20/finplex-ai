#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Checking for obvious committed secret patterns..."

if git ls-files | grep -E '(^|/)\.env$|\.pem$|\.key$|credentials\.json$|service-account.*\.json$'; then
  echo "Potential secret file is tracked. Remove it from Git."
  exit 1
fi

if git grep -n -I -E '(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC |)PRIVATE KEY)' -- . \
  ':(exclude)uv.lock' \
  ':(exclude)package-lock.json'; then
  echo "Potential secret value found. Remove it before merging."
  exit 1
fi

echo "No obvious secret patterns found."

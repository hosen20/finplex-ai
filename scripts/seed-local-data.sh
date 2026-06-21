#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}/services/api"
uv run alembic -c alembic.ini upgrade head

cd "${ROOT_DIR}"
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "FinplexAdmin123!"

uv run --project services/api python scripts/seed_product_data.py "$@"

cat <<'EOF'

Local product data is ready.

Platform admin:
  platform.admin@finplexai.com / FinplexAdmin123!

Tenant users:
  tenant_admin@cedarfinance.com / TenantAdmin123!
  manager@cedarfinance.com / TenantAdmin123!
  reviewer@cedarfinance.com / TenantAdmin123!
  auditor@cedarfinance.com / TenantAdmin123!

  tenant_admin@orionmedical.com / TenantAdmin123!
  manager@orionmedical.com / TenantAdmin123!
  reviewer@orionmedical.com / TenantAdmin123!
  auditor@orionmedical.com / TenantAdmin123!
EOF

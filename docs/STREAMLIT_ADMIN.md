# Streamlit Platform Admin

The Streamlit Platform Admin app is the internal Finplex AI operations console.
It is not a tenant-facing product page and it is not a public sign-up flow.

## Purpose

Platform admins use this app to:

- create tenant companies
- create the first tenant admin for each company
- create additional tenant users when needed
- suspend or reactivate tenants
- inspect API health and readiness

Tenant users continue to use the React web app after their account has been
created by a platform admin or tenant admin.

## Why There Is No Public Sign-Up

Finplex AI handles invoice data, ERP records, CRM notes, debt-collection drafts,
and audit logs. A public self-service sign-up flow would allow uncontrolled
access to sensitive workflows. The local product therefore uses a controlled B2B
onboarding model:

```text
Platform Admin -> Tenant -> First Tenant Admin -> Tenant Users
```

## First-Time Bootstrap

Start infrastructure and apply migrations first. Then create the first platform
admin from the terminal:

```bash
uv run --project services/api alembic -c services/api/alembic.ini upgrade head
uv run --project services/api python scripts/bootstrap-platform-admin.py
```

The command creates an internal platform tenant named
`Finplex Platform Operations` and a `platform_admin` user.

You can also pass values explicitly:

```bash
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "ChangeMe123!"
```

## Running The Admin App

Start the FastAPI backend in one terminal:

```bash
make api
```

Start the Streamlit admin in another terminal:

```bash
make admin
```

Open:

```text
http://localhost:8501
```

## Main Admin Workflow

1. Sign in as the platform admin.
2. Create a tenant/company.
3. Create the first `tenant_admin` user for that tenant.
4. Give the tenant admin credentials to the company user.
5. Tenant users sign in through the React web app.

## Security Notes

- Only `platform_admin` users can list and create tenants.
- Tenant admins cannot create other tenants.
- Tenant admins can manage users only inside their own tenant.
- The React app should not expose platform tenant operations.

# Streamlit Platform Admin

The Streamlit admin app is the internal operational console for Finplex platform administrators.

## Run

Start the API first:

```bash
make api
```

Then start Streamlit:

```bash
make admin
```

Open:

```text
http://localhost:8501
```

## First Login

Create the first platform admin:

```bash
uv run --project services/api python scripts/bootstrap-platform-admin.py \
  --email platform.admin@finplexai.com \
  --full-name "Finplex Platform Admin" \
  --password "FinplexAdmin123!"
```

Log in with that email and password.

## Responsibilities

Platform admins can:

- create tenants
- create first tenant admins
- create users for a tenant when needed
- view tenant status
- suspend tenants
- reactivate tenants
- inspect API health

## Product Boundary

Streamlit is for platform operations. Normal tenant finance users should use the React workspace.

## Recommended Tenant Creation Flow

1. Platform admin creates a tenant.
2. Platform admin creates the first tenant admin.
3. Tenant admin logs in to React.
4. Tenant admin creates managers, reviewers, and auditors.
5. Tenant users work inside the React workspace.

## Security Notes

- Do not share the platform admin password.
- Do not create customer-facing tenant users inside the platform tenant.
- Use realistic but privacy-safe sample data locally.
- Platform admin actions should be auditable.

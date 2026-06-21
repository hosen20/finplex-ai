# Tenant Web App

The React web app is the tenant-facing Finplex AI product. It is not used for public signup and it does not create companies. Company onboarding is controlled by the Streamlit Platform Admin console.

## User Flow

1. A platform admin creates a tenant in Streamlit.
2. A platform admin creates the first tenant admin for that tenant.
3. The tenant admin signs in to the React web app.
4. The tenant admin creates managers, reviewers, and auditors for their own company.
5. Tenant users upload invoices, inspect ERP/CRM evidence, review AI drafts, and approve or reject actions.

## Role Behavior

| Role | React capabilities |
| --- | --- |
| tenant_admin | View workspace, upload invoices, review drafts, and create tenant users. |
| manager | View workspace, upload invoices, and review finance workflows. |
| reviewer | View review queue and make human approval decisions. |
| auditor | Inspect tenant records and evidence without operational actions. |

## Product Boundary

The React app only uses the signed-in user's tenant from the JWT-backed `/auth/me` session. The UI no longer contains hardcoded demo tenants or demo account buttons.

The backend still enforces tenant isolation and RBAC. UI checks are convenience only and are not treated as security controls.

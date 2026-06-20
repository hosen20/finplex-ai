# Finplex AI Demo Accounts

These accounts are created by `scripts/seed_demo_data.py` for the final local demo.

## Tenant

- Tenant ID: `tenant_demo_clinic`
- Tenant Name: `Finplex Demo Clinic Group`

## Admin User

- Email: `clinadmin@example.com`
- Password: `FinplexDemo123!`
- Role: tenant admin
- Demo purpose: show full workspace access, dashboard metrics, invoice upload, invoices, reviews, evidence, and settings.

## Manager User

- Email: `manager@example.com`
- Password: `FinplexDemo123!`
- Role: manager
- Demo purpose: show operational review access and human approval workflow.

## Suggested Login Story

1. Login as the admin account.
2. Show the overview, upload flow, invoice list, evidence center, and review queue.
3. Logout.
4. Login as the manager account.
5. Show that the manager can inspect reviews and handle draft approval decisions.

## Demo Notes

Do not use these credentials outside the local demo environment. They are intentionally simple and only meant for a repeatable capstone presentation.

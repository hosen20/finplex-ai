# Datasets

Finplex AI runs locally with privacy-safe datasets. The product does not require
live ERP or CRM credentials to be reviewed.

## Dataset Inputs

| File | Product role |
|---|---|
| `data/seed/crm_customers.csv` | Customer-level payment behavior and CRM-like risk signals. |
| `data/seed/historical_erp_invoices.csv` | ERP invoice history, due dates, amounts, payment terms, and dispute flags. |
| `data/seed/historical_erp_payments.csv` | ERP payment settlement history. |
| `data/seed/new_uploaded_invoice_ground_truth.csv` | Expected fields for generated invoice images. |
| `data/demo_invoices/new_uploaded_invoices/*.png` | Local invoice images used for upload and extraction testing. |
| `regulations/**` | Policy and governance documents seeded into tenant RAG. |

The customer and payment tables are derived from a public, IBM-style customer
payment dataset preparation workflow. The invoice images are generated local
invoice files used for OCR and extraction testing. The project stores only
privacy-safe local records.

## Seeding Command

Run the seed command after infrastructure is running and migrations are applied:

```bash
bash scripts/seed-local-data.sh
```

The command is idempotent. It creates or updates:

- two local product tenants,
- tenant admins, managers, reviewers, and auditors,
- customers imported from the prepared customer dataset,
- ERP invoices and payments,
- CRM notes and dispute records,
- RAG policy documents and chunks,
- review-ready invoice records with evidence and audit events.

For a clean reseed of only the product tenants:

```bash
bash scripts/seed-local-data.sh --reset-product-tenants
```

This reset does not delete the platform admin account.

## Seeded Accounts

Platform admin:

```text
platform.admin@finplexai.com / FinplexAdmin123!
```

Cedar Finance tenant users:

```text
tenant_admin@cedarfinance.com / TenantAdmin123!
manager@cedarfinance.com / TenantAdmin123!
reviewer@cedarfinance.com / TenantAdmin123!
auditor@cedarfinance.com / TenantAdmin123!
```

Orion Medical tenant users:

```text
tenant_admin@orionmedical.com / TenantAdmin123!
manager@orionmedical.com / TenantAdmin123!
reviewer@orionmedical.com / TenantAdmin123!
auditor@orionmedical.com / TenantAdmin123!
```

## Review Notes

The local seed intentionally creates two tenants so reviewers can verify tenant
isolation. The React tenant workspace should show only the logged-in tenant's
customers, invoices, reviews, and evidence. The Streamlit Platform Admin can see
and manage both tenants.

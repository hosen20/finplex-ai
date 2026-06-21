# Local Product Seed Data

This folder contains privacy-safe local data used to run Finplex AI as a finished
product without external ERP or CRM credentials.

## Source roles

- `crm_customers.csv` contains IBM-style customer/payment behavior features.
- `historical_erp_invoices.csv` simulates ERP invoice history.
- `historical_erp_payments.csv` simulates ERP settlement history.
- `new_uploaded_invoice_ground_truth.csv` maps generated invoice images to
  extracted invoice fields.
- `risk_training_dataset.csv` documents the feature schema used by the risk
  model notebooks and model artifact.

The seed command maps these files into realistic local tenants:

- `tenant_cedar_finance`
- `tenant_orion_medical`

The empty JSON placeholders are kept only as future extension points. The current
source of truth for product seeding is the CSV-backed seeding script:

```bash
bash scripts/seed-local-data.sh
```

For a clean reseed of only the product tenants:

```bash
bash scripts/seed-local-data.sh --reset-product-tenants
```

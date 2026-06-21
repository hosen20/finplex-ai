# Manual Upload Dashboard Demo

This dashboard version is configured for the clean manual upload demo.

## Demo tenant

The dashboard uses:

```text
tenant_demo_clinic
```

## Demo accounts

```text
clinadmin@example.com
manager@example.com
FinplexDemo123!
```

## Upload files

Upload these image files from the dashboard:

```text
data/demo_invoices/manual_upload_images/NEW-00001.png
data/demo_invoices/manual_upload_images/NEW-00002.png
```

`NEW-00001.png` is the approval path.

`NEW-00002.png` is the rejection path.

## Expected flow

1. Login as admin.
2. Upload `NEW-00001.png` with Aurora Medical Supplies.
3. Wait for the worker to create a pending review.
4. Approve the review.
5. Upload `NEW-00002.png` with Northstar Diagnostics Lab.
6. Wait for the worker to create a pending review.
7. Reject the review.

The UI does not show raw JSON. It shows clean status labels, evidence IDs, and draft messages.

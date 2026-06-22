# OCR Invoice Extraction

Finplex AI now treats invoice text extraction as a first-class product step.
The upload request stays fast: the React app uploads a PDF/image/text invoice to
FastAPI, FastAPI stores it, and Kafka triggers the worker to extract text before
calling the model-server pipeline.

## Local-first OCR strategy

The worker uses `LocalOcrService` through `LocalInvoiceTextReader`:

1. Plain-text uploads are read directly.
2. Image/PDF uploads first look for deterministic OCR sidecars in
   `data/demo_invoices/manual_upload_ocr/`.
3. PDFs can use optional `pypdf` extraction when the package is available.
4. Images can use optional local Tesseract via `pytesseract` and `Pillow` when
   those packages and the system binary are available.
5. If no OCR path is available, the worker emits a deterministic fallback text
   so local CI and tests remain stable.

This design is intentionally provider-agnostic. The OCR service can later be
replaced by a stronger OCR engine without changing the upload API, Kafka event,
model-server contract, or React app.

## Pipeline metadata

For traceability, OCR metadata is passed into the model-server pipeline context
and stored under `invoice.extracted_fields.ai_pipeline.ocr`:

- `engine`
- `source`
- `confidence`
- `text_length`

An `ocr_text_extracted` audit event is also recorded for every processed upload.

## Manual test

Use the seeded local product data and upload:

```text
/home/hosen20/finplex-ai/data/demo_invoices/manual_upload_images/NEW-00001.png
```

The worker should read:

```text
data/demo_invoices/manual_upload_ocr/NEW-00001.txt
```

Then the LangGraph model-server pipeline should extract fields, score risk,
retrieve evidence, draft the message, pass guardrails, and create a human review.

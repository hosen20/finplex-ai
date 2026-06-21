from datetime import UTC, datetime

from app.events import InvoiceUploadedEvent
from app.storage import LocalInvoiceTextReader


def make_event(file_name: str, storage_key: str) -> InvoiceUploadedEvent:
    return InvoiceUploadedEvent(
        invoice_id="inv_1",
        tenant_id="tenant_demo_clinic",
        uploaded_by_user_id="user_1",
        file_name=file_name,
        storage_key=storage_key,
        content_type="image/png",
        size_bytes=100,
        event_id="evt_1",
        occurred_at=datetime.now(UTC),
    )


def test_image_upload_reads_matching_ocr_sidecar(tmp_path) -> None:
    storage_dir = tmp_path / "storage"
    sidecar_dir = tmp_path / "manual_upload_ocr"
    sidecar_dir.mkdir(parents=True)
    (sidecar_dir / "NEW-00001.txt").write_text(
        "Invoice number: NEW-00001 Customer: Aurora Medical Supplies",
        encoding="utf-8",
    )

    reader = LocalInvoiceTextReader(
        base_dir=storage_dir,
        ocr_sidecar_dir=sidecar_dir,
    )
    event = make_event(
        file_name="NEW-00001.png",
        storage_key="tenant_demo_clinic/invoices/inv_1/NEW-00001.png",
    )

    text = reader.read_text(event)

    assert "NEW-00001" in text
    assert "Aurora Medical Supplies" in text


def test_text_upload_reads_stored_file(tmp_path) -> None:
    storage_dir = tmp_path / "storage"
    file_path = storage_dir / "tenant_demo_clinic/invoices/inv_1/invoice.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("Invoice number: INV-TEXT", encoding="utf-8")

    reader = LocalInvoiceTextReader(base_dir=storage_dir)
    event = make_event(
        file_name="invoice.txt",
        storage_key="tenant_demo_clinic/invoices/inv_1/invoice.txt",
    )

    assert reader.read_text(event) == "Invoice number: INV-TEXT"

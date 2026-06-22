from datetime import UTC, datetime
from pathlib import Path

from app.events import InvoiceUploadedEvent
from app.services.ocr_service import LocalOcrService
from app.storage import LocalInvoiceTextReader


def test_ocr_service_reads_plain_text_invoice(tmp_path: Path) -> None:
    invoice_path = tmp_path / "invoice.txt"
    invoice_path.write_text("Invoice Number: TXT-1 Total: 250.00", encoding="utf-8")

    result = LocalOcrService().extract_text(
        file_path=invoice_path,
        file_name="invoice.txt",
        content_type="text/plain",
        invoice_id="inv_txt_1",
    )

    assert result.engine == "plain_text_reader"
    assert result.confidence == 0.99
    assert "TXT-1" in result.text


def test_ocr_service_prefers_image_sidecar(tmp_path: Path) -> None:
    image_path = tmp_path / "NEW-00001.png"
    image_path.write_bytes(b"not a real image needed for sidecar test")
    sidecar_dir = tmp_path / "ocr"
    sidecar_dir.mkdir()
    (sidecar_dir / "NEW-00001.txt").write_text(
        "Invoice Number: OCR-1 Customer: Cedar Clinic Total: 900.00",
        encoding="utf-8",
    )

    result = LocalOcrService().extract_text(
        file_path=image_path,
        file_name="NEW-00001.png",
        content_type="image/png",
        invoice_id="inv_ocr_1",
        sidecar_dir=sidecar_dir,
    )

    assert result.engine == "local_ocr_sidecar"
    assert result.confidence == 0.92
    assert "OCR-1" in result.text
    assert result.to_pipeline_metadata()["text_length"] == len(result.text)


def test_local_invoice_text_reader_returns_ocr_result(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    sidecar_dir = tmp_path / "sidecars"
    storage_dir.mkdir()
    sidecar_dir.mkdir()

    storage_key = "tenant_1/invoices/inv_1/NEW-00002.png"
    invoice_path = storage_dir / storage_key
    invoice_path.parent.mkdir(parents=True)
    invoice_path.write_bytes(b"image bytes")
    (sidecar_dir / "NEW-00002.txt").write_text(
        "Invoice Number: OCR-2 Customer: Orion Medical Total: 1500.00",
        encoding="utf-8",
    )

    event = InvoiceUploadedEvent(
        invoice_id="inv_1",
        tenant_id="tenant_1",
        uploaded_by_user_id="user_1",
        file_name="NEW-00002.png",
        storage_key=storage_key,
        content_type="image/png",
        size_bytes=128,
        event_id="evt_1",
        occurred_at=datetime.now(UTC),
    )

    reader = LocalInvoiceTextReader(
        base_dir=storage_dir,
        ocr_sidecar_dir=sidecar_dir,
    )
    result = reader.read_result(event)

    assert result.engine == "local_ocr_sidecar"
    assert "OCR-2" in reader.read_text(event)

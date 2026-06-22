from pathlib import Path

from app.config import ROOT_DIR, settings
from app.events import InvoiceUploadedEvent
from app.services.ocr_service import LocalOcrService, OcrResult


class LocalInvoiceTextReader:
    """Reads locally stored invoice text through the OCR service.

    Image/PDF uploads first look for deterministic OCR sidecars under
    data/demo_invoices/manual_upload_ocr/. If no sidecar exists, the OCR service
    can use optional local OCR libraries or a safe fallback for CI.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        ocr_sidecar_dir: Path | None = None,
        ocr_service: LocalOcrService | None = None,
    ) -> None:
        self.base_dir = base_dir or settings.local_storage_dir
        self.ocr_sidecar_dir = (
            ocr_sidecar_dir
            or ROOT_DIR / "data" / "demo_invoices" / "manual_upload_ocr"
        )
        self.ocr_service = ocr_service or LocalOcrService()

    def read_text(self, event: InvoiceUploadedEvent) -> str:
        return self.read_result(event).text

    def read_result(self, event: InvoiceUploadedEvent) -> OcrResult:
        file_path = self.base_dir / event.storage_key
        return self.ocr_service.extract_text(
            file_path=file_path,
            file_name=event.file_name,
            content_type=event.content_type,
            invoice_id=event.invoice_id,
            sidecar_dir=self.ocr_sidecar_dir,
        )

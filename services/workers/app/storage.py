from pathlib import Path

from app.config import ROOT_DIR, settings
from app.events import InvoiceUploadedEvent

_TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt", ".xml"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}


class LocalInvoiceTextReader:
    """Reads locally stored invoice text or demo OCR sidecars.

    The real dashboard demo uploads invoice images. To keep the local demo
    deterministic on a CPU-only laptop, image uploads can be paired with a
    text sidecar under data/demo_invoices/manual_upload_ocr/<file-stem>.txt.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        ocr_sidecar_dir: Path | None = None,
    ) -> None:
        self.base_dir = base_dir or settings.local_storage_dir
        self.ocr_sidecar_dir = (
            ocr_sidecar_dir
            or ROOT_DIR / "data" / "demo_invoices" / "manual_upload_ocr"
        )

    def read_text(self, event: InvoiceUploadedEvent) -> str:
        file_path = self.base_dir / event.storage_key
        suffix = file_path.suffix.lower() or Path(event.file_name).suffix.lower()

        if file_path.exists() and suffix in _TEXT_SUFFIXES:
            return file_path.read_text(encoding="utf-8", errors="ignore")

        if suffix in _IMAGE_SUFFIXES:
            sidecar_path = self._matching_sidecar_path(event, file_path)
            if sidecar_path.exists():
                return sidecar_path.read_text(encoding="utf-8", errors="ignore")

        return (
            f"Invoice number: {event.invoice_id}. "
            f"Customer: Customer. "
            f"File name: {event.file_name}. "
            "Payment terms: Net 30."
        )

    def _matching_sidecar_path(
        self,
        event: InvoiceUploadedEvent,
        file_path: Path,
    ) -> Path:
        file_name_stem = Path(event.file_name).stem
        storage_stem = file_path.stem

        candidates = [
            self.ocr_sidecar_dir / f"{file_name_stem}.txt",
            self.ocr_sidecar_dir / f"{storage_stem}.txt",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0]

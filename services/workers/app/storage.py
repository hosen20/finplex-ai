from pathlib import Path

from app.config import settings
from app.events import InvoiceUploadedEvent

_TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt", ".xml"}


class LocalInvoiceTextReader:
    """Reads locally stored invoice text when possible."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.local_storage_dir

    def read_text(self, event: InvoiceUploadedEvent) -> str:
        file_path = self.base_dir / event.storage_key

        if file_path.exists() and file_path.suffix.lower() in _TEXT_SUFFIXES:
            return file_path.read_text(encoding="utf-8", errors="ignore")

        return (
            f"Invoice number: {event.invoice_id}. "
            f"Customer: Customer. "
            f"File name: {event.file_name}. "
            "Payment terms: Net 30."
        )
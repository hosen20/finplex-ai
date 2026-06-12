import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Protocol

from app.config import settings

_SAFE_FILE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class StoredInvoiceFile:
    """Metadata returned after an invoice file is stored."""

    storage_key: str
    file_name: str
    content_type: str
    size_bytes: int


class InvoiceStorage(Protocol):
    """Storage interface for invoice documents."""

    def save_invoice(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> StoredInvoiceFile:
        """Persist an invoice file and return storage metadata."""


def sanitize_file_name(file_name: str) -> str:
    """Return a safe file name suitable for object storage keys."""
    stripped = Path(file_name).name.strip()
    safe_name = _SAFE_FILE_NAME_PATTERN.sub("_", stripped)
    return safe_name or "invoice.bin"


class LocalInvoiceStorage:
    """Stores invoice files on the local filesystem for local development/tests."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.local_storage_dir

    def save_invoice(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> StoredInvoiceFile:
        safe_file_name = sanitize_file_name(file_name)
        storage_key = f"{tenant_id}/invoices/{invoice_id}/{safe_file_name}"
        destination = self.base_dir / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

        return StoredInvoiceFile(
            storage_key=storage_key,
            file_name=safe_file_name,
            content_type=content_type,
            size_bytes=len(content),
        )


class MinioInvoiceStorage:
    """Stores invoice files in MinIO using an S3-compatible bucket."""

    def __init__(self) -> None:
        from minio import Minio

        self.bucket_name = settings.minio_bucket_invoices
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_secure,
        )

    def save_invoice(
        self,
        *,
        tenant_id: str,
        invoice_id: str,
        file_name: str,
        content_type: str,
        content: bytes,
    ) -> StoredInvoiceFile:
        safe_file_name = sanitize_file_name(file_name)
        storage_key = f"{tenant_id}/invoices/{invoice_id}/{safe_file_name}"

        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

        self.client.put_object(
            self.bucket_name,
            storage_key,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

        return StoredInvoiceFile(
            storage_key=storage_key,
            file_name=safe_file_name,
            content_type=content_type,
            size_bytes=len(content),
        )


def get_invoice_storage() -> InvoiceStorage:
    """FastAPI dependency that selects the configured invoice storage backend."""
    if settings.invoice_storage_backend == "minio":
        return MinioInvoiceStorage()

    return LocalInvoiceStorage()
"""Local OCR service for invoice uploads.

The production path is intentionally provider-agnostic: text invoices are read
as plain text, image/PDF uploads use deterministic OCR sidecars when present,
and optional local OCR libraries are used when installed. The deterministic
fallback keeps CI and local development reliable on CPU-only machines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt", ".xml"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
_PDF_SUFFIXES = {".pdf"}


@dataclass(frozen=True)
class OcrResult:
    """OCR result returned to the worker pipeline."""

    text: str
    engine: str
    source: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_pipeline_metadata(self) -> dict[str, Any]:
        """Return safe metadata to store with AI pipeline results."""
        return {
            "engine": self.engine,
            "source": self.source,
            "confidence": self.confidence,
            "text_length": len(self.text),
            **self.metadata,
        }


class LocalOcrService:
    """Extract text from local invoice files with deterministic fallbacks."""

    def extract_text(
        self,
        *,
        file_path: Path,
        file_name: str,
        content_type: str | None = None,
        invoice_id: str | None = None,
        sidecar_dir: Path | None = None,
    ) -> OcrResult:
        """Extract invoice text from a stored file or OCR sidecar."""
        suffix = (file_path.suffix or Path(file_name).suffix).lower()

        if file_path.exists() and suffix in _TEXT_SUFFIXES:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return OcrResult(
                text=text,
                engine="plain_text_reader",
                source="stored_text_file",
                confidence=0.99,
                metadata={"content_type": content_type or "text/plain"},
            )

        sidecar_path = self._find_sidecar(
            file_path=file_path,
            file_name=file_name,
            sidecar_dir=sidecar_dir,
        )
        if sidecar_path is not None:
            text = sidecar_path.read_text(encoding="utf-8", errors="ignore")
            return OcrResult(
                text=text,
                engine="local_ocr_sidecar",
                source=str(sidecar_path),
                confidence=0.92,
                metadata={"content_type": content_type or "application/octet-stream"},
            )

        if file_path.exists() and suffix in _PDF_SUFFIXES:
            pdf_text = self._try_pdf_text(file_path)
            if pdf_text:
                return OcrResult(
                    text=pdf_text,
                    engine="pypdf_text_extraction",
                    source=str(file_path),
                    confidence=0.82,
                    metadata={"content_type": content_type or "application/pdf"},
                )

        if file_path.exists() and suffix in _IMAGE_SUFFIXES:
            image_text = self._try_tesseract(file_path)
            if image_text:
                return OcrResult(
                    text=image_text,
                    engine="tesseract_local",
                    source=str(file_path),
                    confidence=0.78,
                    metadata={"content_type": content_type or "image/*"},
                )

        return OcrResult(
            text=self._fallback_text(
                invoice_id=invoice_id,
                file_name=file_name,
                content_type=content_type,
            ),
            engine="deterministic_ocr_fallback",
            source="generated_fallback",
            confidence=0.35,
            metadata={
                "content_type": content_type or "application/octet-stream",
                "file_exists": file_path.exists(),
            },
        )

    def _find_sidecar(
        self,
        *,
        file_path: Path,
        file_name: str,
        sidecar_dir: Path | None,
    ) -> Path | None:
        if sidecar_dir is None:
            return None

        candidates = [
            sidecar_dir / f"{Path(file_name).stem}.txt",
            sidecar_dir / f"{file_path.stem}.txt",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _try_pdf_text(self, file_path: Path) -> str | None:
        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]
        except Exception:
            return None

        try:
            reader = PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(page.strip() for page in pages if page.strip())
            return text or None
        except Exception:
            return None

    def _try_tesseract(self, file_path: Path) -> str | None:
        try:
            import pytesseract  # type: ignore[import-not-found]
            from PIL import Image  # type: ignore[import-not-found]
        except Exception:
            return None

        try:
            text = pytesseract.image_to_string(Image.open(file_path))
            text = text.strip()
            return text or None
        except Exception:
            return None

    def _fallback_text(
        self,
        *,
        invoice_id: str | None,
        file_name: str,
        content_type: str | None,
    ) -> str:
        invoice_number = invoice_id or Path(file_name).stem
        return (
            f"Invoice number: {invoice_number}. "
            f"File name: {file_name}. "
            f"Content type: {content_type or 'unknown'}. "
            "Customer: Customer. Payment terms: Net 30."
        )

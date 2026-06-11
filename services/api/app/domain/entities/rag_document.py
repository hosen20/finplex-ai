from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class RagDocument:
    document_id: str
    tenant_id: str
    title: str
    source_type: str
    storage_key: str
    created_at: datetime = datetime.now(UTC)


@dataclass(slots=True)
class RagChunk:
    chunk_id: str
    tenant_id: str
    document_id: str
    content: str
    chunk_index: int
    embedding_id: str | None = None

    def preview(self, max_length: int = 120) -> str:
        if len(self.content) <= max_length:
            return self.content
        return f"{self.content[:max_length].rstrip()}..."
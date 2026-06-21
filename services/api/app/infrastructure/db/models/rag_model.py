from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models.base import Base, TimestampMixin
from app.infrastructure.db.types import PgVectorType

RAG_EMBEDDING_DIMENSIONS = 8


class RagDocumentModel(Base, TimestampMixin):
    __tablename__ = "rag_documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)


class RagChunkModel(Base, TimestampMixin):
    __tablename__ = "rag_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("rag_documents.document_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    embedding: Mapped[list[float] | dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    embedding_vector: Mapped[list[float] | None] = mapped_column(
        PgVectorType(RAG_EMBEDDING_DIMENSIONS),
        nullable=True,
    )

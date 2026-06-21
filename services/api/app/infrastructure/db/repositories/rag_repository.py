"""Repository helpers for tenant-scoped RAG retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.db.models.rag_model import RagChunkModel, RagDocumentModel
from app.infrastructure.db.types import format_pgvector


@dataclass(frozen=True)
class RagSearchResult:
    chunk_id: str
    tenant_id: str
    document_id: str
    document_title: str
    source_type: str
    content: str
    chunk_index: int
    score: float


class RagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_document(self, document: RagDocumentModel) -> RagDocumentModel:
        self.session.add(document)
        self.session.flush()
        return document

    def add_chunk(self, chunk: RagChunkModel) -> RagChunkModel:
        self.session.add(chunk)
        self.session.flush()
        return chunk

    def search_by_embedding(
        self,
        *,
        tenant_id: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[RagSearchResult]:
        """Return nearest tenant-scoped chunks using pgvector cosine distance."""

        safe_limit = max(1, min(limit, 20))
        query_vector = format_pgvector(query_embedding)
        rows = self.session.execute(
            text(
                """
                SELECT
                    c.chunk_id,
                    c.tenant_id,
                    c.document_id,
                    d.title AS document_title,
                    d.source_type,
                    c.content,
                    c.chunk_index,
                    1 - (c.embedding_vector <=> CAST(:query_vector AS vector))
                        AS score
                FROM rag_chunks AS c
                JOIN rag_documents AS d
                    ON d.document_id = c.document_id
                WHERE c.tenant_id = :tenant_id
                  AND d.tenant_id = :tenant_id
                  AND c.embedding_vector IS NOT NULL
                ORDER BY c.embedding_vector <=> CAST(:query_vector AS vector)
                LIMIT :limit
                """
            ),
            {
                "tenant_id": tenant_id,
                "query_vector": query_vector,
                "limit": safe_limit,
            },
        ).mappings()

        return [
            RagSearchResult(
                chunk_id=str(row["chunk_id"]),
                tenant_id=str(row["tenant_id"]),
                document_id=str(row["document_id"]),
                document_title=str(row["document_title"]),
                source_type=str(row["source_type"]),
                content=str(row["content"]),
                chunk_index=int(row["chunk_index"]),
                score=float(row["score"] or 0.0),
            )
            for row in rows
        ]

    def list_chunks_by_tenant(self, tenant_id: str) -> list[RagChunkModel]:
        return (
            self.session.query(RagChunkModel)
            .filter(RagChunkModel.tenant_id == tenant_id)
            .order_by(RagChunkModel.document_id, RagChunkModel.chunk_index)
            .all()
        )

"""Application service for tenant-scoped RAG search."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.infrastructure.db.repositories.rag_repository import (
    RagRepository,
    RagSearchResult,
)
from sqlalchemy.orm import Session

RAG_EMBEDDING_DIMENSIONS = 8


@dataclass(frozen=True)
class RagEvidence:
    chunk_id: str
    document_id: str
    document_title: str
    source_type: str
    content: str
    score: float


def deterministic_embedding(
    text_value: str,
    dimensions: int = RAG_EMBEDDING_DIMENSIONS,
) -> list[float]:
    """Return a stable local embedding for tests, seed data, and offline use.

    This keeps the local product reproducible. A model-provider embedding can
    replace this function later without changing the database contract.
    """

    digest = hashlib.sha256(text_value.encode("utf-8")).digest()
    return [round(digest[index] / 255, 6) for index in range(dimensions)]


class RagService:
    def __init__(self, session: Session) -> None:
        self.repository = RagRepository(session)

    def search(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int = 5,
    ) -> list[RagEvidence]:
        if not query.strip():
            return []

        query_embedding = deterministic_embedding(query)
        results = self.repository.search_by_embedding(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            limit=limit,
        )
        return [self._to_evidence(result) for result in results]

    @staticmethod
    def _to_evidence(result: RagSearchResult) -> RagEvidence:
        return RagEvidence(
            chunk_id=result.chunk_id,
            document_id=result.document_id,
            document_title=result.document_title,
            source_type=result.source_type,
            content=result.content,
            score=round(result.score, 6),
        )

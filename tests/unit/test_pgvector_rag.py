from app.application.services.rag_service import RagService, deterministic_embedding
from app.infrastructure.db.repositories.rag_repository import (
    RagRepository,
    RagSearchResult,
)
from app.infrastructure.db.types import format_pgvector


def test_format_pgvector_uses_pgvector_text_format() -> None:
    assert format_pgvector([0.1, 0.25, 1]) == "[0.100000,0.250000,1.000000]"


def test_deterministic_embedding_is_stable() -> None:
    first = deterministic_embedding("human approval required")
    second = deterministic_embedding("human approval required")

    assert first == second
    assert len(first) == 8
    assert all(0 <= value <= 1 for value in first)


def test_rag_service_search_is_tenant_scoped(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_search_by_embedding(
        self: RagRepository,
        *,
        tenant_id: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[RagSearchResult]:
        captured["tenant_id"] = tenant_id
        captured["query_embedding"] = query_embedding
        captured["limit"] = limit
        return [
            RagSearchResult(
                chunk_id="rag_tenant_a_policy_000",
                tenant_id=tenant_id,
                document_id="ragdoc_tenant_a_policy",
                document_title="Human Approval Policy",
                source_type="policy_document",
                content="Human approval is required before customer follow-up.",
                chunk_index=0,
                score=0.91,
            )
        ]

    monkeypatch.setattr(RagRepository, "search_by_embedding", fake_search_by_embedding)

    results = RagService(session=object()).search(
        tenant_id="tenant_a",
        query="What must be approved before sending a payment follow-up?",
        limit=3,
    )

    assert captured["tenant_id"] == "tenant_a"
    assert captured["limit"] == 3
    assert len(captured["query_embedding"]) == 8
    assert results[0].chunk_id == "rag_tenant_a_policy_000"
    assert results[0].score == 0.91

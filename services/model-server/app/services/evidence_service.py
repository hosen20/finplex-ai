from app.config import settings
from app.rag import EvidenceMatch, HybridEvidenceStore
from app.schemas import (
    EvidenceCitation,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
)


class EvidenceService:
    """Retrieves traceable evidence using the local hybrid RAG store."""

    def __init__(self, evidence_store: HybridEvidenceStore | None = None) -> None:
        self.evidence_store = evidence_store or HybridEvidenceStore()

    def search(self, request: EvidenceSearchRequest) -> EvidenceSearchResponse:
        matches = self.evidence_store.search(
            query=request.query,
            source_types=request.source_types,
            top_k=request.top_k,
        )
        citations = [self._to_citation(match) for match in matches]

        return EvidenceSearchResponse(
            tenant_id=request.tenant_id,
            invoice_id=request.invoice_id,
            query=request.query,
            citations=citations,
            evidence_ids=[citation.evidence_id for citation in citations],
            retrieval_method="hybrid_sparse_dense_local",
            model_version=settings.pipeline_version,
        )

    def _to_citation(self, match: EvidenceMatch) -> EvidenceCitation:
        chunk = match.chunk

        metadata = {
            **chunk.metadata,
            "sparse_score": match.sparse_score,
            "dense_score": match.dense_score,
            "exact_match_score": match.exact_match_score,
            "source_boost": match.source_boost,
            "matched_terms": match.matched_terms,
        }

        return EvidenceCitation(
            evidence_id=chunk.evidence_id,
            source_type=chunk.source_type,
            title=chunk.title,
            snippet=chunk.snippet(),
            score=match.score,
            metadata=metadata,
        )
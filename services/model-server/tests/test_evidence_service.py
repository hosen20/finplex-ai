from pathlib import Path

from app.rag import HybridEvidenceStore
from app.schemas import EvidenceSearchRequest
from app.services.evidence_service import EvidenceService


def build_store(tmp_path: Path) -> HybridEvidenceStore:
    regulations_dir = tmp_path / "regulations"
    seed_dir = tmp_path / "data" / "seed"

    regulations_dir.mkdir(parents=True)
    seed_dir.mkdir(parents=True)

    (regulations_dir / "debt_collection_policy.md").write_text(
        "\n".join(
            [
                "# Debt Collection Policy",
                "Collection drafts must avoid threats, harassment, and false",
                "legal claims. If a customer has a dispute, the draft should",
                "ask for clarification and remain respectful.",
            ]
        ),
        encoding="utf-8",
    )

    (seed_dir / "historical_erp_payments.csv").write_text(
        "\n".join(
            [
                "invoice_number,customer_name,status,days_late,amount_due",
                "INV-1,Acme,late,14,1200",
                "INV-2,Acme,paid,0,800",
            ]
        ),
        encoding="utf-8",
    )

    (seed_dir / "crm_customers.csv").write_text(
        "\n".join(
            [
                "customer_name,crm_note,dispute_flag",
                "Acme,Customer requested payment timing support,true",
                "Beta,Customer usually pays on time,false",
            ]
        ),
        encoding="utf-8",
    )

    return HybridEvidenceStore(
        regulations_dir=regulations_dir,
        seed_dir=seed_dir,
        chunk_size_chars=500,
        semantic_dimensions=4,
    )


def test_evidence_service_returns_citations(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    service = EvidenceService(evidence_store=store)

    response = service.search(
        EvidenceSearchRequest(
            tenant_id="tenant_1",
            invoice_id="INV-1",
            query="Acme late payment dispute respectful collection policy",
            source_types=["regulation", "erp", "crm"],
            top_k=3,
        )
    )

    assert response.tenant_id == "tenant_1"
    assert response.invoice_id == "INV-1"
    assert response.retrieval_method == "hybrid_sparse_dense_local"
    assert response.citations
    assert response.evidence_ids == [
        citation.evidence_id for citation in response.citations
    ]

    first_citation = response.citations[0]

    assert first_citation.evidence_id.startswith("ev_")
    assert first_citation.source_type in {"regulation", "erp", "crm"}
    assert first_citation.score > 0
    assert "sparse_score" in first_citation.metadata
    assert "dense_score" in first_citation.metadata
    assert "exact_match_score" in first_citation.metadata


def test_hybrid_store_filters_by_source_type(tmp_path: Path) -> None:
    store = build_store(tmp_path)

    matches = store.search(
        query="Acme late payment amount due",
        source_types=["erp"],
        top_k=5,
    )

    assert matches
    assert all(match.chunk.source_type == "erp" for match in matches)


def test_hybrid_store_falls_back_when_query_has_no_overlap(
    tmp_path: Path,
) -> None:
    store = build_store(tmp_path)

    matches = store.search(
        query="zzzzzz unknown unrelated phrase",
        source_types=["regulation"],
        top_k=2,
    )

    assert matches
    assert all(match.chunk.source_type == "regulation" for match in matches)
from pathlib import Path

from app.rag import HybridEvidenceStore


def build_hybrid_store(tmp_path: Path) -> HybridEvidenceStore:
    regulations_dir = tmp_path / "regulations"
    seed_dir = tmp_path / "data" / "seed"

    regulations_dir.mkdir(parents=True)
    seed_dir.mkdir(parents=True)

    (regulations_dir / "fdcpa_policy.md").write_text(
        "\n".join(
            [
                "# Responsible Collection Policy",
                "Debt collection messages must avoid threats, harassment,",
                "false legal claims, and misleading statements.",
                "All AI-generated collection drafts require human review.",
            ]
        ),
        encoding="utf-8",
    )

    (seed_dir / "historical_erp_payments.csv").write_text(
        "\n".join(
            [
                "invoice_number,customer_name,status,days_late,amount_due",
                "INV-100,Acme,late,21,15000",
                "INV-101,Acme,paid,0,9000",
            ]
        ),
        encoding="utf-8",
    )

    (seed_dir / "crm_customers.csv").write_text(
        "\n".join(
            [
                "customer_name,crm_note,dispute_flag",
                "Acme,Customer reported a billing dispute,true",
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


def test_hybrid_store_returns_score_breakdown(tmp_path: Path) -> None:
    store = build_hybrid_store(tmp_path)

    matches = store.search(
        query="Acme late invoice dispute responsible collection",
        source_types=["regulation", "erp", "crm"],
        top_k=3,
    )

    assert matches

    first_match = matches[0]

    assert first_match.score > 0
    assert first_match.sparse_score >= 0
    assert first_match.dense_score >= 0
    assert first_match.exact_match_score >= 0
    assert first_match.source_boost >= 1
    assert first_match.chunk.evidence_id.startswith("ev_")
    assert first_match.chunk.metadata["retrieval_method"] == (
        "hybrid_sparse_dense_local"
    )


def test_hybrid_store_respects_source_filter(tmp_path: Path) -> None:
    store = build_hybrid_store(tmp_path)

    matches = store.search(
        query="Acme late invoice amount due",
        source_types=["erp"],
        top_k=5,
    )

    assert matches
    assert all(match.chunk.source_type == "erp" for match in matches)


def test_hybrid_store_can_return_regulation_evidence(tmp_path: Path) -> None:
    store = build_hybrid_store(tmp_path)

    matches = store.search(
        query="human review threats harassment legal claims",
        source_types=["regulation"],
        top_k=3,
    )

    assert matches
    assert all(match.chunk.source_type == "regulation" for match in matches)
    assert any("human review" in match.chunk.content.lower() for match in matches)


def test_hybrid_store_fallback_is_source_filtered(tmp_path: Path) -> None:
    store = build_hybrid_store(tmp_path)

    matches = store.search(
        query="zzzzzz unrelated query with no overlap",
        source_types=["crm"],
        top_k=2,
    )

    assert matches
    assert all(match.chunk.source_type == "crm" for match in matches)
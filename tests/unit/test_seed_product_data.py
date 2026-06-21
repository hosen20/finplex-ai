import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.seed_product_data import (  # noqa: E402
    RiskLevel,
    chunk_text,
    deterministic_embedding,
    relationship_status,
    risk_level_for_customer,
)


def test_deterministic_embedding_is_stable() -> None:
    first = deterministic_embedding("human approval required")
    second = deterministic_embedding("human approval required")

    assert first == second
    assert len(first) == 8
    assert all(0 <= value <= 1 for value in first)


def test_chunk_text_keeps_content_in_order() -> None:
    text = "first paragraph\n\nsecond paragraph\n\nthird paragraph"

    chunks = chunk_text(text, max_chars=24)

    assert chunks == ["first paragraph", "second paragraph", "third paragraph"]


def test_customer_risk_helpers_use_late_and_dispute_signals() -> None:
    row = {
        "previous_late_payments": "9",
        "disputed_invoice_count": "1",
        "crm_negative_signal_score": "0.12",
    }

    assert relationship_status(row) == "at_risk"
    assert risk_level_for_customer(row) == RiskLevel.HIGH

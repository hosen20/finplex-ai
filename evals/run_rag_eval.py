"""Run tenant RAG retrieval golden evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evals.common import (
    EvalResult,
    exit_for_result,
    load_json,
    load_thresholds,
    safe_divide,
    tokenize,
)

GOLDEN_PATH = Path("data/golden/rag_questions.json")


def retrieve_documents(
    question: str,
    documents: list[dict[str, str]],
    *,
    top_k: int = 3,
) -> list[dict[str, str]]:
    """Rank documents by simple lexical overlap for deterministic CI checks."""
    question_tokens = tokenize(question)

    scored_documents = []
    for document in documents:
        content_tokens = tokenize(f"{document['title']} {document['content']}")
        overlap = len(question_tokens & content_tokens)
        scored_documents.append((overlap, document["document_id"], document))

    scored_documents.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored_documents[:top_k]]


def evaluate() -> EvalResult:
    """Evaluate hit@3 and required-term coverage."""
    data = load_json(GOLDEN_PATH)
    thresholds = load_thresholds()
    cases: list[dict[str, Any]] = data["cases"]

    hits = 0
    required_terms_found = 0
    required_terms_total = 0
    failures: list[str] = []

    for case in cases:
        retrieved = retrieve_documents(case["question"], case["documents"], top_k=3)
        retrieved_ids = {document["document_id"] for document in retrieved}
        expected_ids = set(case["expected_doc_ids"])

        if retrieved_ids & expected_ids:
            hits += 1
        else:
            failures.append(
                
                    f"{case['case_id']}: expected one of {sorted(expected_ids)}, "
                    f"got {sorted(retrieved_ids)}"
                
            )

        retrieved_text = " ".join(document["content"] for document in retrieved)
        retrieved_tokens = tokenize(retrieved_text)
        for term in case["required_terms"]:
            required_terms_total += 1
            if tokenize(term) <= retrieved_tokens:
                required_terms_found += 1
            else:
                failures.append(f"{case['case_id']}: missing required term {term!r}")

    hit_at_3 = hits / len(cases)
    term_coverage = safe_divide(required_terms_found, required_terms_total)
    hit_minimum = thresholds.get("rag_hit_at_3_min", 0.8)
    term_minimum = thresholds.get("rag_required_term_coverage_min", 0.8)
    passed = hit_at_3 >= hit_minimum and term_coverage >= term_minimum

    return EvalResult(
        name="rag_eval",
        metrics={
            "hit_at_3": hit_at_3,
            "required_term_coverage": term_coverage,
        },
        passed=passed,
        failures=[] if passed else failures,
    )


if __name__ == "__main__":
    exit_for_result(evaluate())

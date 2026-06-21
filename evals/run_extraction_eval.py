"""Run deterministic invoice extraction golden evaluation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from evals.common import EvalResult, exit_for_result, load_json, load_thresholds

GOLDEN_PATH = Path("data/golden/extraction_expected.json")


def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip().rstrip(".")
    return ""


def extract_invoice_fields(ocr_text: str) -> dict[str, str]:
    """Extract invoice fields from OCR text using deterministic regexes."""
    invoice_number = _first_match(
        [
            r"invoice\s*(?:number|no|#)?\s*[:#-]\s*([A-Z0-9-]+)",
            r"\b(INV-[A-Z0-9-]+)\b",
        ],
        ocr_text,
    )
    supplier = _first_match(
        [r"supplier\s*:\s*([^\n]+)", r"vendor\s*:\s*([^\n]+)"],
        ocr_text,
    )
    customer = _first_match(
        [r"customer\s*:\s*([^\n]+)", r"bill\s+to\s*:\s*([^\n]+)"],
        ocr_text,
    )
    invoice_date = _first_match([r"invoice\s+date\s*:\s*(\d{4}-\d{2}-\d{2})"], ocr_text)
    due_date = _first_match(
        [
            r"due\s+date\s*:\s*(\d{4}-\d{2}-\d{2})",
            r"payment\s+due\s*:\s*(\d{4}-\d{2}-\d{2})",
        ],
        ocr_text,
    )
    amount = _first_match(
        [
            r"(?:total\s+amount|amount\s+due|balance\s+due)\s*:\s*(?:USD\s*)?\$?([0-9,]+\.\d{2})",
        ],
        ocr_text,
    ).replace(",", "")
    currency = "USD" if re.search(r"\bUSD\b|\$", ocr_text, re.IGNORECASE) else ""

    return {
        "invoice_number": invoice_number,
        "supplier": supplier,
        "customer": customer,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "currency": currency,
        "total_amount": amount,
    }


def evaluate() -> EvalResult:
    """Evaluate extraction field accuracy against the golden set."""
    data = load_json(GOLDEN_PATH)
    thresholds = load_thresholds()
    cases: list[dict[str, Any]] = data["cases"]

    total_fields = 0
    matched_fields = 0
    failures: list[str] = []

    for case in cases:
        predicted = extract_invoice_fields(case["ocr_text"])
        expected = case["expected"]
        for field_name, expected_value in expected.items():
            total_fields += 1
            actual_value = predicted.get(field_name, "")
            if actual_value == expected_value:
                matched_fields += 1
            else:
                failures.append(
                    
                        f"{case['case_id']} {field_name}: "
                        f"expected {expected_value!r}, got {actual_value!r}"
                    
                )

    accuracy = matched_fields / total_fields
    minimum = thresholds.get("extraction_field_accuracy_min", 0.85)

    return EvalResult(
        name="extraction_eval",
        metrics={"field_accuracy": accuracy},
        passed=accuracy >= minimum,
        failures=[] if accuracy >= minimum else failures,
    )


if __name__ == "__main__":
    exit_for_result(evaluate())

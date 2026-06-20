from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import httpx

API_URL = os.getenv("FINPLEX_API_URL", "http://localhost:8000").rstrip("/")
MODEL_SERVER_URL = os.getenv("FINPLEX_MODEL_SERVER_URL", "http://localhost:8001").rstrip("/")
GUARDRAILS_URL = os.getenv("FINPLEX_GUARDRAILS_URL", "http://localhost:8002").rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("FINPLEX_DEMO_TIMEOUT_SECONDS", "20"))

TENANT_ID = "tenant_demo_clinic"
INVOICE_ID = "inv_demo_high_001"
CUSTOMER_NAME = "Aurora Medical Supplies"
CONTACT_NAME = "Maya Haddad"
INVOICE_NUMBER = "NEW-00001"
AMOUNT_DUE = 12450.00
CURRENCY = "USD"
DUE_DATE = "2026-05-29"


@dataclass(frozen=True)
class StepResult:
    name: str
    ok: bool
    detail: str


class DemoFlowError(RuntimeError):
    """Raised when the demo smoke flow cannot continue."""


def main() -> None:
    print_header()
    results: list[StepResult] = []

    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        results.extend(check_health(client))
        extraction = extract_invoice(client)
        results.append(
            StepResult(
                name="invoice extraction",
                ok=True,
                detail=(
                    f"invoice={extraction['extracted_fields'].get('invoice_number')} "
                    f"confidence={extraction.get('confidence')}"
                ),
            )
        )

        risk = score_risk(client, extraction)
        results.append(
            StepResult(
                name="risk scoring",
                ok=True,
                detail=(
                    f"risk={risk.get('risk_level')} "
                    f"score={risk.get('risk_score')} "
                    f"model={risk.get('model_name')}"
                ),
            )
        )

        evidence = search_evidence(client, risk)
        results.append(
            StepResult(
                name="hybrid RAG evidence",
                ok=True,
                detail=(
                    f"citations={len(evidence.get('citations', []))} "
                    f"method={evidence.get('retrieval_method')}"
                ),
            )
        )

        draft = draft_message(client, risk, evidence)
        results.append(
            StepResult(
                name="draft generation",
                ok=True,
                detail=(
                    f"characters={len(draft.get('draft_message', ''))} "
                    f"citations={len(draft.get('citations', []))}"
                ),
            )
        )

        guardrails = validate_guardrails(client, draft, risk)
        results.append(
            StepResult(
                name="guardrails validation",
                ok=bool(guardrails.get("passed")),
                detail=(
                    f"decision={guardrails.get('decision')} "
                    f"findings={len(guardrails.get('findings', []))} "
                    f"nemo_passed={guardrails.get('nemo_passed')}"
                ),
            )
        )

        pipeline = run_full_pipeline(client)
        results.append(
            StepResult(
                name="full model-server pipeline",
                ok=True,
                detail=(
                    f"risk={pipeline['risk'].get('risk_level')} "
                    f"pipeline_citations={len(pipeline.get('citations', []))}"
                ),
            )
        )

    print_results(results)
    print_demo_summary(extraction, risk, evidence, draft, guardrails, pipeline)



def print_header() -> None:
    print("\nFinplex AI demo smoke flow")
    print("=" * 32)
    print(f"API:          {API_URL}")
    print(f"Model-server: {MODEL_SERVER_URL}")
    print(f"Guardrails:   {GUARDRAILS_URL}\n")



def check_health(client: httpx.Client) -> list[StepResult]:
    checks = [
        ("api health", f"{API_URL}/health"),
        ("model-server health", f"{MODEL_SERVER_URL}/health"),
        ("guardrails health", f"{GUARDRAILS_URL}/health"),
    ]
    results: list[StepResult] = []

    for name, url in checks:
        response = client.get(url)
        require_success(response, name)
        payload = response.json()
        results.append(
            StepResult(
                name=name,
                ok=True,
                detail=f"status={payload.get('status', 'unknown')}",
            )
        )

    return results



def extract_invoice(client: httpx.Client) -> dict[str, Any]:
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "file_name": "NEW-00001.png",
        "text": (
            "Invoice NEW-00001 for Aurora Medical Supplies. "
            "Amount due is 12450.00 USD. Due date is 2026-05-29. "
            "The customer has requested clarification about pricing."
        ),
    }
    response = client.post(f"{MODEL_SERVER_URL}/extract-invoice", json=payload)
    require_success(response, "invoice extraction")
    return response.json()



def score_risk(client: httpx.Client, extraction: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "extracted_fields": extraction.get("extracted_fields", {}),
        "days_overdue": 21,
        "has_dispute": True,
        "previous_late_payments": 5,
        "customer_relationship_status": "at_risk",
        "risk_features": {
            "amount_due": AMOUNT_DUE,
            "payment_terms_days": 30,
            "paperless_bill": 1,
            "country_code": "USA",
            "previous_invoice_count": 14,
            "previous_late_payments": 5,
            "previous_disputed_count": 2,
            "previous_total_amount": 87250.00,
            "previous_average_invoice_amount": 6232.14,
            "previous_average_days_late": 12.5,
            "previous_max_days_late": 34.0,
            "previous_on_time_payment_rate": 0.55,
            "previous_dispute_rate": 0.14,
            "previous_crm_negative_signal_score": 0.78,
            "relationship_age_days": 720,
        },
    }
    response = client.post(f"{MODEL_SERVER_URL}/score-risk", json=payload)
    require_success(response, "risk scoring")
    return response.json()



def search_evidence(client: httpx.Client, risk: dict[str, Any]) -> dict[str, Any]:
    reasons = "; ".join(risk.get("reasons", []))
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "query": (
            "Aurora Medical Supplies NEW-00001 12450 USD overdue "
            "pricing dispute CRM ERP responsible collection follow-up "
            f"{risk.get('risk_level', '')} {reasons}"
        ),
        "source_types": ["regulation", "erp", "crm", "invoice"],
        "top_k": 5,
        "context": {
            "risk_level": risk.get("risk_level"),
            "risk_score": risk.get("risk_score"),
            "invoice_number": INVOICE_NUMBER,
            "customer_name": CUSTOMER_NAME,
        },
    }
    response = client.post(f"{MODEL_SERVER_URL}/search-evidence", json=payload)
    require_success(response, "hybrid RAG evidence")
    return response.json()



def draft_message(
    client: httpx.Client,
    risk: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    evidence_ids = sorted(
        set(risk.get("evidence_ids", [])) | set(evidence.get("evidence_ids", []))
    )
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "customer_name": CUSTOMER_NAME,
        "contact_name": CONTACT_NAME,
        "invoice_number": INVOICE_NUMBER,
        "amount_due": AMOUNT_DUE,
        "currency": CURRENCY,
        "due_date": DUE_DATE,
        "risk_level": risk.get("risk_level", "high"),
        "evidence_ids": evidence_ids,
        "evidence_context": evidence.get("citations", []),
    }
    response = client.post(f"{MODEL_SERVER_URL}/draft-message", json=payload)
    require_success(response, "draft generation")
    return response.json()



def validate_guardrails(
    client: httpx.Client,
    draft: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "draft_message": draft.get("draft_message", ""),
        "risk_level": risk.get("risk_level", "high"),
        "evidence_ids": draft.get("evidence_ids", []),
        "customer_name": CUSTOMER_NAME,
        "amount_due": AMOUNT_DUE,
        "metadata": {
            "invoice_number": INVOICE_NUMBER,
            "demo_flow": True,
        },
    }
    response = client.post(f"{GUARDRAILS_URL}/validate-message", json=payload)
    require_success(response, "guardrails validation")
    return response.json()



def run_full_pipeline(client: httpx.Client) -> dict[str, Any]:
    payload = {
        "tenant_id": TENANT_ID,
        "invoice_id": INVOICE_ID,
        "file_name": "NEW-00001.png",
        "text": (
            "Invoice NEW-00001 for Aurora Medical Supplies. "
            "Amount due is 12450.00 USD. Due date is 2026-05-29. "
            "There is an open pricing dispute and the account is overdue."
        ),
        "days_overdue": 21,
        "has_dispute": True,
        "previous_late_payments": 5,
        "customer_relationship_status": "at_risk",
        "risk_features": {
            "amount_due": AMOUNT_DUE,
            "payment_terms_days": 30,
            "paperless_bill": 1,
            "country_code": "USA",
            "previous_invoice_count": 14,
            "previous_late_payments": 5,
            "previous_disputed_count": 2,
            "previous_total_amount": 87250.00,
            "previous_average_invoice_amount": 6232.14,
            "previous_average_days_late": 12.5,
            "previous_max_days_late": 34.0,
            "previous_on_time_payment_rate": 0.55,
            "previous_dispute_rate": 0.14,
            "previous_crm_negative_signal_score": 0.78,
            "relationship_age_days": 720,
        },
    }
    response = client.post(f"{MODEL_SERVER_URL}/process-invoice", json=payload)
    require_success(response, "full model-server pipeline")
    return response.json()



def require_success(response: httpx.Response, step_name: str) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = response.text[:1000]
        raise DemoFlowError(
            f"{step_name} failed with HTTP {response.status_code}: {detail}"
        ) from exc



def print_results(results: list[StepResult]) -> None:
    print("Demo checks")
    print("-" * 32)
    for result in results:
        marker = "PASS" if result.ok else "WARN"
        print(f"[{marker}] {result.name}: {result.detail}")



def print_demo_summary(
    extraction: dict[str, Any],
    risk: dict[str, Any],
    evidence: dict[str, Any],
    draft: dict[str, Any],
    guardrails: dict[str, Any],
    pipeline: dict[str, Any],
) -> None:
    print("\nDemo story summary")
    print("-" * 32)
    print(f"Customer:        {CUSTOMER_NAME}")
    print(f"Invoice:         {INVOICE_NUMBER}")
    print(f"Amount due:      {AMOUNT_DUE:.2f} {CURRENCY}")
    print(f"Risk:            {risk.get('risk_level')} ({risk.get('risk_score')})")
    print(f"Evidence items:  {len(evidence.get('citations', []))}")
    print(f"Guardrails:      {guardrails.get('decision')}")
    print(f"Pipeline draft:  {len(pipeline['draft'].get('draft_message', ''))} chars")

    draft_preview = " ".join(draft.get("draft_message", "").split())
    if len(draft_preview) > 260:
        draft_preview = f"{draft_preview[:260].rstrip()}..."

    print("\nDraft preview")
    print("-" * 32)
    print(draft_preview)

    print("\nTop evidence")
    print("-" * 32)
    for citation in evidence.get("citations", [])[:3]:
        print(
            f"- {citation.get('evidence_id')} "
            f"({citation.get('source_type')}): {citation.get('title')}"
        )

    print("\nFull compact JSON result")
    print("-" * 32)
    compact = {
        "extraction_confidence": extraction.get("confidence"),
        "risk_level": risk.get("risk_level"),
        "risk_score": risk.get("risk_score"),
        "evidence_ids": evidence.get("evidence_ids", [])[:5],
        "guardrails_passed": guardrails.get("passed"),
        "human_review_required": guardrails.get("human_review_required"),
    }
    print(json.dumps(compact, indent=2))
    print("\nDemo smoke flow completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        print("\nDemo flow could not connect to one of the services.", file=sys.stderr)
        print(
            "Make sure API, model-server, and guardrails are running.",
            file=sys.stderr,
        )
        print(f"Details: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except DemoFlowError as exc:
        print(f"\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc

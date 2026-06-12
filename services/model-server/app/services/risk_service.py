from app.config import settings
from app.schemas import RiskScoreRequest, RiskScoreResponse


class RiskScoringService:
    """Deterministic placeholder late-payment risk scorer."""

    def score(self, request: RiskScoreRequest) -> RiskScoreResponse:
        score = 0.15
        reasons: list[str] = []

        if request.days_overdue >= 60:
            score += 0.45
            reasons.append("Invoice is 60 or more days overdue.")
        elif request.days_overdue >= 30:
            score += 0.3
            reasons.append("Invoice is 30 or more days overdue.")
        elif request.days_overdue > 0:
            score += 0.15
            reasons.append("Invoice is overdue.")

        if request.has_dispute:
            score += 0.25
            reasons.append("CRM history indicates an active dispute.")

        if request.previous_late_payments:
            score += min(request.previous_late_payments * 0.08, 0.24)
            reasons.append("Customer has previous late payments.")

        if request.customer_relationship_status in {"at_risk", "strained"}:
            score += 0.15
            reasons.append("Customer relationship status is marked as at risk.")

        score = min(score, 0.99)
        risk_level = self._risk_level(score)

        if not reasons:
            reasons.append("No major late-payment or dispute signals were found.")

        return RiskScoreResponse(
            invoice_id=request.invoice_id,
            tenant_id=request.tenant_id,
            risk_level=risk_level,
            risk_score=round(score, 2),
            reasons=reasons,
            model_version=settings.pipeline_version,
        )

    def _risk_level(self, score: float):
        if score >= 0.85:
            return "critical"
        if score >= 0.65:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"
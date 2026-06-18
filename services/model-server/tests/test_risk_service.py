from pathlib import Path

import joblib
from app.schemas import RiskFeaturePayload, RiskScoreRequest
from app.services.risk_service import RiskScoringService


class FakeRiskModel:
    classes_ = ["low", "medium", "high", "critical"]

    def predict(self, feature_frame):
        assert "amount_due" in feature_frame.columns
        return ["high"]

    def predict_proba(self, feature_frame):
        assert "previous_late_payments" in feature_frame.columns
        return [[0.05, 0.10, 0.80, 0.05]]


def build_payload() -> RiskFeaturePayload:
    return RiskFeaturePayload(
        amount_due=13600.0,
        payment_terms_days=30,
        paperless_bill=0,
        country_code="US",
        previous_invoice_count=12,
        previous_late_payments=5,
        previous_disputed_count=2,
        previous_total_amount=120000.0,
        previous_average_invoice_amount=10000.0,
        previous_average_days_late=9.5,
        previous_max_days_late=34.0,
        previous_on_time_payment_rate=0.58,
        previous_dispute_rate=0.16,
        previous_crm_negative_signal_score=0.42,
        relationship_age_days=950,
    )


def build_request(features: RiskFeaturePayload) -> RiskScoreRequest:
    return RiskScoreRequest(
        invoice_id="new_inv_001",
        tenant_id="tenant_demo",
        risk_features=features,
    )


def test_risk_service_uses_fallback_when_model_is_missing(tmp_path: Path) -> None:
    service = RiskScoringService(
        model_path=tmp_path / "missing.joblib",
        feature_schema_path=tmp_path / "missing_schema.json",
        label_mapping_path=tmp_path / "missing_labels.json",
        metadata_path=tmp_path / "missing_metadata.json",
    )

    result = service.score(build_request(build_payload()))

    assert result.model_loaded is False
    assert result.risk_level in {"low", "medium", "high", "critical"}
    assert result.feature_source == "deterministic_fallback"
    assert result.top_risk_signals


def test_risk_service_loads_real_model_artifact(tmp_path: Path) -> None:
    model_path = tmp_path / "risk_model.joblib"
    schema_path = tmp_path / "risk_feature_schema.json"
    labels_path = tmp_path / "risk_label_mapping.json"
    metadata_path = tmp_path / "risk_model_metadata.json"

    joblib.dump(FakeRiskModel(), model_path)

    schema_path.write_text(
        """
        {
          "feature_columns": [
            "amount_due",
            "payment_terms_days",
            "paperless_bill",
            "country_code",
            "previous_invoice_count",
            "previous_late_payments",
            "previous_disputed_count",
            "previous_total_amount",
            "previous_average_invoice_amount",
            "previous_average_days_late",
            "previous_max_days_late",
            "previous_on_time_payment_rate",
            "previous_dispute_rate",
            "previous_crm_negative_signal_score",
            "relationship_age_days"
          ]
        }
        """,
        encoding="utf-8",
    )

    labels_path.write_text(
        '{"labels": ["low", "medium", "high", "critical"]}',
        encoding="utf-8",
    )

    metadata_path.write_text(
        '{"model_name": "fake_random_forest", "created_at": "test"}',
        encoding="utf-8",
    )

    service = RiskScoringService(
        model_path=model_path,
        feature_schema_path=schema_path,
        label_mapping_path=labels_path,
        metadata_path=metadata_path,
    )

    result = service.score(build_request(build_payload()))

    assert result.model_loaded is True
    assert result.risk_level == "high"
    assert result.risk_score == 0.8
    assert result.probabilities["high"] == 0.8
    assert result.model_name == "fake_random_forest"
    assert result.feature_source == "trained_notebook_artifact"
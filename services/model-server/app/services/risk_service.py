from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.config import settings
from app.schemas import (
    RiskFeaturePayload,
    RiskScoreRequest,
    RiskScoreResponse,
    RiskSignal,
)

DEFAULT_FEATURE_COLUMNS = [
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
    "relationship_age_days",
]

DEFAULT_LABELS = ["low", "medium", "high", "critical"]


class RiskScoringService:
    """Scores invoice risk using the trained artifact when feature payloads exist."""

    def __init__(
        self,
        model_path: Path | None = None,
        feature_schema_path: Path | None = None,
        label_mapping_path: Path | None = None,
        metadata_path: Path | None = None,
    ) -> None:
        self.model_path = model_path or settings.risk_model_path
        self.feature_schema_path = (
            feature_schema_path or settings.risk_feature_schema_path
        )
        self.label_mapping_path = (
            label_mapping_path or settings.risk_label_mapping_path
        )
        self.metadata_path = metadata_path or settings.risk_model_metadata_path

        self._model: Any | None = None
        self._feature_columns: list[str] = DEFAULT_FEATURE_COLUMNS.copy()
        self._labels: list[str] = DEFAULT_LABELS.copy()
        self._metadata: dict[str, Any] = {}
        self._load_error: str | None = None

        self.load_artifacts()

    @property
    def model_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def model_name(self) -> str:
        if self.model_loaded:
            return str(self._metadata.get("model_name", "notebook_risk_model"))

        return "deterministic_fallback"

    @property
    def model_version(self) -> str:
        if self.model_loaded:
            return str(self._metadata.get("created_at", "notebook_02_artifact"))

        return settings.pipeline_version

    def load_artifacts(self) -> None:
        self._load_error = None

        try:
            if self.feature_schema_path.exists():
                feature_schema = self._read_json(self.feature_schema_path)
                self._feature_columns = feature_schema.get(
                    "feature_columns",
                    DEFAULT_FEATURE_COLUMNS,
                )

            if self.label_mapping_path.exists():
                label_mapping = self._read_json(self.label_mapping_path)
                self._labels = label_mapping.get("labels", DEFAULT_LABELS)

            if self.metadata_path.exists():
                self._metadata = self._read_json(self.metadata_path)

            if self.model_path.exists():
                self._model = joblib.load(self.model_path)
            else:
                self._model = None
                self._load_error = f"Model artifact not found: {self.model_path}"

        except Exception as exc:
            self._model = None
            self._load_error = str(exc)

    def score(self, request: RiskScoreRequest) -> RiskScoreResponse:
        if request.risk_features is not None:
            return self._score_feature_payload(request, request.risk_features)

        return self._score_legacy_payload(request)

    def _score_feature_payload(
        self,
        request: RiskScoreRequest,
        features: RiskFeaturePayload,
    ) -> RiskScoreResponse:
        feature_values = features.model_dump()
        feature_frame = self._build_feature_frame(feature_values)

        if self.model_loaded:
            predicted_label = str(self._model.predict(feature_frame)[0])
            probabilities = self._predict_probabilities(
                feature_frame,
                predicted_label,
            )
            confidence = float(probabilities.get(predicted_label, 1.0))
            risk_score = confidence
            feature_source = "trained_notebook_artifact"
        else:
            fallback_score = self._fallback_numeric_score(feature_values)
            predicted_label = self._score_to_label(fallback_score)
            risk_score = round(fallback_score / 100, 4)
            probabilities = {label: 0.0 for label in self._labels}
            probabilities[predicted_label] = 1.0
            feature_source = "deterministic_fallback"

        signals = self._build_top_risk_signals(feature_values)
        reasons = [signal.reason for signal in signals]

        return RiskScoreResponse(
            invoice_id=request.invoice_id,
            tenant_id=request.tenant_id,
            risk_level=predicted_label,
            risk_score=round(risk_score, 4),
            reasons=reasons,
            evidence_ids=[f"ev_{request.invoice_id}_risk"],
            model_version=self.model_version,
            model_loaded=self.model_loaded,
            model_name=self.model_name,
            probabilities=probabilities,
            feature_source=feature_source,
            top_risk_signals=signals,
        )

    def _score_legacy_payload(self, request: RiskScoreRequest) -> RiskScoreResponse:
        risk_points = 0.0
        reasons: list[str] = []

        if request.days_overdue >= 60:
            risk_points += 0.45
            reasons.append("Invoice is more than 60 days overdue.")
        elif request.days_overdue >= 30:
            risk_points += 0.30
            reasons.append("Invoice is more than 30 days overdue.")
        elif request.days_overdue > 0:
            risk_points += 0.15
            reasons.append("Invoice is currently overdue.")

        if request.has_dispute:
            risk_points += 0.25
            reasons.append("Customer has an open dispute signal.")

        if request.previous_late_payments > 0:
            added_score = min(request.previous_late_payments * 0.12, 0.30)
            risk_points += added_score
            reasons.append("Customer has previous late-payment history.")

        if request.customer_relationship_status.lower() in {"new", "at_risk"}:
            risk_points += 0.10
            reasons.append("Customer relationship status needs closer review.")

        risk_score = min(risk_points, 1.0)
        risk_level = self._risk_score_to_legacy_label(risk_score)

        if not reasons:
            reasons.append("No major historical risk signals were found.")

        return RiskScoreResponse(
            invoice_id=request.invoice_id,
            tenant_id=request.tenant_id,
            risk_level=risk_level,
            risk_score=round(risk_score, 4),
            reasons=reasons,
            evidence_ids=[f"ev_{request.invoice_id}_risk"],
            model_version=settings.pipeline_version,
            model_loaded=False,
            model_name="deterministic_fallback",
            probabilities={risk_level: 1.0},
            feature_source="legacy_rule_features",
            top_risk_signals=[
                RiskSignal(
                    name="legacy_rules",
                    value=risk_level,
                    reason=reason,
                )
                for reason in reasons[:5]
            ],
        )

    def _build_feature_frame(self, feature_values: dict[str, Any]) -> pd.DataFrame:
        missing_features = [
            column
            for column in self._feature_columns
            if column not in feature_values
        ]

        if missing_features:
            missing_text = ", ".join(missing_features)
            raise ValueError(f"Missing model features: {missing_text}")

        ordered_values = {
            column: feature_values[column]
            for column in self._feature_columns
        }

        return pd.DataFrame([ordered_values], columns=self._feature_columns)

    def _predict_probabilities(
        self,
        feature_frame: pd.DataFrame,
        predicted_label: str,
    ) -> dict[str, float]:
        if not hasattr(self._model, "predict_proba"):
            return {predicted_label: 1.0}

        raw_probabilities = self._model.predict_proba(feature_frame)[0]
        classes = [str(class_label) for class_label in self._model.classes_]

        return {
            class_label: round(float(probability), 4)
            for class_label, probability in zip(
                classes,
                raw_probabilities,
                strict=False,
            )
        }

    def _fallback_numeric_score(self, feature_values: dict[str, Any]) -> float:
        score = 0.0

        score += min(feature_values["previous_late_payments"] / 10, 1.0) * 24
        score += min(feature_values["previous_average_days_late"] / 45, 1.0) * 18
        score += min(feature_values["previous_max_days_late"] / 90, 1.0) * 12
        score += (1 - feature_values["previous_on_time_payment_rate"]) * 18
        score += feature_values["previous_dispute_rate"] * 10
        score += feature_values["previous_crm_negative_signal_score"] * 12

        amount_due = feature_values["amount_due"]
        previous_average = max(feature_values["previous_average_invoice_amount"], 1)
        score += min(amount_due / previous_average, 3.0) / 3.0 * 6

        return round(min(score, 100), 2)

    def _score_to_label(self, score: float) -> str:
        if score < 25:
            return "low"

        if score < 50:
            return "medium"

        if score < 75:
            return "high"

        return "critical"

    def _risk_score_to_legacy_label(self, score: float) -> str:
        if score < 0.25:
            return "low"

        if score < 0.50:
            return "medium"

        if score < 0.75:
            return "high"

        return "critical"

    def _build_top_risk_signals(
        self,
        feature_values: dict[str, Any],
    ) -> list[RiskSignal]:
        signals: list[RiskSignal] = []

        if feature_values["previous_late_payments"] > 0:
            signals.append(
                RiskSignal(
                    name="previous_late_payments",
                    value=feature_values["previous_late_payments"],
                    reason="Customer has previous late-payment history.",
                )
            )

        if feature_values["previous_average_days_late"] > 0:
            signals.append(
                RiskSignal(
                    name="previous_average_days_late",
                    value=feature_values["previous_average_days_late"],
                    reason="Customer's historical invoices were late on average.",
                )
            )

        if feature_values["previous_on_time_payment_rate"] < 0.8:
            signals.append(
                RiskSignal(
                    name="previous_on_time_payment_rate",
                    value=feature_values["previous_on_time_payment_rate"],
                    reason="Customer has a lower historical on-time payment rate.",
                )
            )

        if feature_values["previous_dispute_rate"] > 0:
            signals.append(
                RiskSignal(
                    name="previous_dispute_rate",
                    value=feature_values["previous_dispute_rate"],
                    reason="Customer has previous disputed invoices.",
                )
            )

        if feature_values["previous_crm_negative_signal_score"] > 0:
            signals.append(
                RiskSignal(
                    name="previous_crm_negative_signal_score",
                    value=feature_values["previous_crm_negative_signal_score"],
                    reason="CRM history contains negative payment or dispute signals.",
                )
            )

        if not signals:
            signals.append(
                RiskSignal(
                    name="clean_payment_history",
                    value="low_signal",
                    reason="No major historical risk signals were found.",
                )
            )

        return signals[:5]

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
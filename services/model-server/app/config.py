from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the Finplex model server."""

    app_name: str = "Finplex AI Model Server"
    environment: str = "local"
    pipeline_version: str = "model_server_v0.1.0"

    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"

    guardrails_url: str = "http://localhost:8002"

    risk_model_path: Path = ROOT_DIR / "models" / "risk_model.joblib"
    risk_feature_schema_path: Path = (
        ROOT_DIR / "models" / "risk_feature_schema.json"
    )
    risk_label_mapping_path: Path = (
        ROOT_DIR / "models" / "risk_label_mapping.json"
    )
    risk_model_metadata_path: Path = (
        ROOT_DIR / "models" / "risk_model_metadata.json"
    )

    evidence_regulations_dir: Path = ROOT_DIR / "regulations"
    evidence_seed_dir: Path = ROOT_DIR / "data" / "seed"
    evidence_max_results: int = 5
    evidence_chunk_size_chars: int = 900

    rag_sparse_weight: float = 0.45
    rag_dense_weight: float = 0.35
    rag_exact_match_weight: float = 0.20
    rag_semantic_dimensions: int = 64

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
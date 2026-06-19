from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for local Finplex workers."""

    app_name: str = "Finplex AI Workers"
    environment: str = "local"

    database_url: str = (
        "postgresql+psycopg://finplex:finplex_password"
        "@localhost:5432/finplex"
    )

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_invoice_uploaded_topic: str = "invoice.uploaded"
    kafka_consumer_group_id: str = "finplex-invoice-workers"
    kafka_client_id: str = "finplex-workers"
    kafka_auto_offset_reset: str = "earliest"

    api_url: str = "http://localhost:8000"
    model_server_url: str = "http://localhost:8001"
    guardrails_url: str = "http://localhost:8002"

    local_storage_dir: Path = ROOT_DIR / "storage" / "local"
    model_server_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
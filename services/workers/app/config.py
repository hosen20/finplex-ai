from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for local Finplex workers."""

    app_name: str = "Finplex AI Workers"
    environment: str = "local"

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_invoice_uploaded_topic: str = "invoice.uploaded"

    api_url: str = "http://localhost:8000"
    model_server_url: str = "http://localhost:8001"
    guardrails_url: str = "http://localhost:8002"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
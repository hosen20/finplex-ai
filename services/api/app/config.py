from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the Finplex API."""

    app_name: str = "Finplex AI API"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://finplex:finplex_password@localhost:5432/finplex"
    redis_url: str = "redis://localhost:6379/0"

    kafka_bootstrap_servers: str = "localhost:29092"
    kafka_invoice_uploaded_topic: str = "invoice.uploaded"

    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "finplex_minio"
    minio_root_password: str = "finplex_minio_password"
    minio_bucket_invoices: str = "finplex-invoices"
    minio_secure: bool = False

    model_server_url: str = "http://localhost:8001"
    guardrails_url: str = "http://localhost:8002"

    erp_provider: str = "local"
    crm_provider: str = "local"

    local_storage_dir: Path = ROOT_DIR / "storage" / "local"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
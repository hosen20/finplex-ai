from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the Finplex model server."""

    app_name: str = "Finplex AI Model Server"
    environment: str = "local"

    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"

    guardrails_url: str = "http://localhost:8002"
    pipeline_version: str = "rules-v0.1"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
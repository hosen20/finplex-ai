from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the guardrails service."""

    app_name: str = "Finplex AI Guardrails"
    environment: str = "local"
    policy_version: str = "guardrails_policy_v0.1.0"

    regulations_dir: Path = ROOT_DIR / "regulations"
    nemo_config_dir: Path = ROOT_DIR / "services" / "guardrails" / "nemo_config"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
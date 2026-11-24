"""Application settings loaded from environment variables (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration with safe defaults for local development."""

    app_name: str = "shorty-api"
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./shorty.db"
    rate_limit_max_requests: int = 10
    rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

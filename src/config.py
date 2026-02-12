from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # MongoDB
    mongodb_uri: str
    mongo_db_name: str = "pigmeu"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM providers
    openai_api_key: str = ""
    groq_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None

    # WordPress
    wordpress_url: Optional[str] = None
    wordpress_username: Optional[str] = None
    wordpress_password: Optional[str] = None

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

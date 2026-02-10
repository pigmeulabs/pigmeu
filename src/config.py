from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables."""
    
    # MongoDB
    mongodb_uri: str
    mongo_db_name: str = "pigmeu"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # OpenAI
    openai_api_key: str
    
    # WordPress
    wordpress_url: Optional[str] = None
    wordpress_username: Optional[str] = None
    wordpress_password: Optional[str] = None
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

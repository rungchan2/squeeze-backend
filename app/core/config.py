from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Squeeze Backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # API
    API_V1_STR: str = "/api/v1"

    # Redis
    REDIS_URL: str
    REDIS_TTL: int = 604800  # 7 days in seconds

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    PROJECT_ID: str

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Text Analysis
    MAX_TEXT_LENGTH: int = 2000
    MIN_TEXT_LENGTH: int = 200
    MAX_WORD_FREQ: int = 50
    MIN_WORD_FREQ: int = 30

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

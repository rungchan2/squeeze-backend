from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


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
    ALLOWED_ORIGINS: str = ""  # Comma-separated list of allowed origins
    BACKEND_CORS_ORIGINS: list[str] = ["*"]  # Deprecated, use ALLOWED_ORIGINS

    # Text Analysis
    MAX_TEXT_LENGTH: int = 2000
    MIN_TEXT_LENGTH: int = 200
    MAX_WORD_FREQ: int = 50
    MIN_WORD_FREQ: int = 30

    @property
    def cors_origins(self) -> List[str]:
        """
        Get allowed CORS origins, including localhost by default
        """
        # Default localhost origins for development
        default_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ]
        
        # Parse custom origins from environment variable
        if self.ALLOWED_ORIGINS:
            custom_origins = [
                origin.strip() 
                for origin in self.ALLOWED_ORIGINS.split(",") 
                if origin.strip()
            ]
            # Combine default and custom origins, removing duplicates
            all_origins = list(set(default_origins + custom_origins))
            return all_origins
        
        return default_origins

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

"""
Application configuration using Pydantic settings.
Loads environment variables from .env file.
"""

import json

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "CareerIQ"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI Career Intelligence Platform"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database — SQLite for demo/hackathon (override with MySQL DATABASE_URL in production)
    DATABASE_URL: str = "sqlite:///./careeriq.db"
    DATABASE_ECHO: bool = False

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"

    # CORS — allow local dev + production Vercel frontend
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000","https://career-iq-muxu-ten.vercel.app"]'
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS JSON string into a list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

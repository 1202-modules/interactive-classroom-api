"""Configuration settings for API service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API
    API_TITLE: str = "Interactive Classroom Platform API"
    API_VERSION: str = "1.0.0"
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "interactive_classroom"
    DB_ECHO: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    
    # Email (for verification codes)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Verification code settings
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    VERIFICATION_CODE_LENGTH: int = 6
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


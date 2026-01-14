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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Cookie settings
    COOKIE_NAME: str = "refresh-token"
    COOKIE_HTTP_ONLY: bool = True
    COOKIE_SECURE: bool = True  # Set to True in production (HTTPS only)
    COOKIE_SAME_SITE: str = "lax"  # Options: "strict", "lax", "none"
    COOKIE_MAX_AGE: int = 604800  # 7 days in seconds
    
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


import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bot-sok API"
    VERSION: str = "1.0.0"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "bot-sok")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_URL: str = os.getenv("MINIO_URL", "http://localhost:9000")
    # Internal URL for Docker communication (defaults to external URL if not set)
    MINIO_INTERNAL_URL: str = os.getenv("MINIO_INTERNAL_URL", "http://minio:9000")
    # Public URL for external access (defaults to MINIO_URL if not set)
    MINIO_PUBLIC_URL: str = os.getenv("MINIO_PUBLIC_URL", os.getenv("MINIO_URL", "http://localhost:9000"))
    
    # Allegro API
    ALLEGRO_CLIENT_ID: str = os.getenv("ALLEGRO_CLIENT_ID", "")
    ALLEGRO_CLIENT_SECRET: str = os.getenv("ALLEGRO_CLIENT_SECRET", "")
    
    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Google Gemini (for Asystenci AI users)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # NGROK
    NGROK_AUTHTOKEN: str = os.getenv("NGROK_AUTHTOKEN", "")
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Email Configuration
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@vsprint.pl")
    MAIL_USE_TLS: bool = True
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Default Admin
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@vsprint.pl")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMeOnFirstLogin123!")
    
    # Asystenciai Integration
    ASYSTENCIAI_SHARED_SECRET: str = os.getenv("ASYSTENCIAI_SHARED_SECRET") or "change-me-in-production"
    ASYSTENCIAI_SETUP_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ASYSTENCIAI_SETUP_TOKEN_EXPIRE_MINUTES") or "30")


settings = Settings() 

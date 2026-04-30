"""
Configuration Management
Loads environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application Settings"""
    
    # Project Info
    PROJECT_NAME: str = "USM Autoimmune ML Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://usm_db_admin:password@localhost:5432/usm_autoimmune_registry")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    TAILSCALE_IP: str = os.getenv("TAILSCALE_IP", "100.106.132.15")
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/data/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "/data/processed")
    RAW_DIR: str = os.getenv("RAW_DIR", "/data/raw")
    
    # ML Model Paths
    MODELS_DIR: str = "/models"
    
    # MinIO Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", os.getenv("MINIO_SECRET_KEY", "minioadmin"))
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    # GPU Configuration
    CUDA_VISIBLE_DEVICES: str = os.getenv("CUDA_VISIBLE_DEVICES", "0")
    
    # Ethics & Compliance
    ETHICS_CLEARANCE_RECEIVED: bool = os.getenv("ETHICS_CLEARANCE_RECEIVED", "false").lower() == "true"
    NMRR_REGISTRATION_NUMBER: str = os.getenv("NMRR_REGISTRATION_NUMBER", "PENDING_USM_ETHICS_CLEARANCE")
    
    class Config:
        case_sensitive = True


settings = Settings()

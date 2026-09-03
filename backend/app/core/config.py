"""
Application Configuration and Environment Settings for VoiceShield Backend.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "VoiceShield"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security & Auth
    JWT_SECRET: str = "voiceshield_super_secret_production_key_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "voiceshield"

    # ML & Storage Paths
    DATASET_DIR: str = "./datasets"
    MODEL_DIR: str = "./models"
    CHECKPOINT_DIR: str = "./checkpoints"
    MANIFEST_DIR: str = "./data/manifests"
    REPORTS_DIR: str = "./reports"

    # ML Training & Automation
    AUTO_TRAIN: bool = False
    MODEL_NAME: str = "AASIST"
    DEVICE: str = "auto"
    STT_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Ensure standard working directories exist
for folder in [settings.DATASET_DIR, settings.MODEL_DIR, settings.CHECKPOINT_DIR, settings.MANIFEST_DIR, settings.REPORTS_DIR]:
    os.makedirs(folder, exist_ok=True)

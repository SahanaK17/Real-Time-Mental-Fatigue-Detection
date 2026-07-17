"""
Application Configuration — Pydantic Settings
==============================================
All configuration values are loaded from environment variables.
Provides type safety, validation, and defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────
    APP_NAME: str = "Mental Fatigue Detector"
    APP_ENV: str = "development"  # development | staging | production
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "changeme-this-is-not-secure"

    # ── API ───────────────────────────────────────────────
    API_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8002
    BACKEND_WORKERS: int = 4

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ── Database ──────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "mental_fatigue_db"
    POSTGRES_USER: str = "mf_user"
    POSTGRES_PASSWORD: str = "mf_secure_password_change_me"
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @model_validator(mode="after")
    def assemble_db_url(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            # Convert sync URL to async
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self

    # ── Redis ─────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @model_validator(mode="after")
    def assemble_redis_url(self) -> "Settings":
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return self

    # ── JWT ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "changeme-jwt-secret-not-secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── ML ────────────────────────────────────────────────
    ML_MODEL_PATH: str = "/app/ml/models/best_model.joblib"
    ML_SCALER_PATH: str = "/app/ml/models/scaler.joblib"
    ML_FEATURE_NAMES_PATH: str = "/app/ml/models/feature_names.json"
    ML_INFERENCE_THRESHOLD: float = 0.5
    SHAP_BACKGROUND_SAMPLES: int = 100

    # ── Email ─────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "Mental Fatigue Detector"
    SMTP_FROM_EMAIL: str = "noreply@mentalfatigue.app"
    EMAIL_ALERTS_ENABLED: bool = False

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # ── Logging ───────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/app/logs/backend.log"

    # ── Notifications ─────────────────────────────────────
    FATIGUE_ALERT_THRESHOLD: float = 0.7
    HIGH_RISK_ALERT_THRESHOLD: float = 0.85

    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()

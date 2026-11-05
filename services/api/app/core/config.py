from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# services/api/app/core/config.py -> repository root is 4 levels up
REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    jwt_secret_key: SecretStr = SecretStr("change-this-local-secret")
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 7
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    database_url: str = (
        "postgresql://smartgrocery:smartgrocery@localhost:5432/smartgrocery"
    )

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env.lower() == "production":
            secret = self.jwt_secret_key.get_secret_value()
            if secret == "change-this-local-secret" or len(secret) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
        return self

    @property
    def sqlalchemy_url(self) -> str:
        # SQLAlchemy needs an explicit driver name for psycopg v3.
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

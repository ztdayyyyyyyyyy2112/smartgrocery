import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", jwt_secret_key="change-this-local-secret")


def test_production_accepts_long_jwt_secret() -> None:
    settings = Settings(app_env="production", jwt_secret_key="x" * 32)
    assert settings.jwt_secret_key.get_secret_value() == "x" * 32

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings.

    Secrets belong in deployment configuration and must never be committed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PACE_",
        extra="ignore",
    )

    app_name: str = "Pace API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/v1"
    docs_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


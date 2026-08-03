from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "E-Card Service API"
    environment: str = "development"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    database_url: str
    secret_key: str

    allowed_origins: str = ""

    public_base_url: str = "http://localhost:5173"

    docs_enabled: bool = True
    redoc_enabled: bool = True

    db_echo: bool = False

    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")

        return value

    @property
    def allowed_origins_list(self) -> list[str]:
        if not self.allowed_origins:
            return []

        origins: list[str] = []

        for origin in self.allowed_origins.split(","):
            cleaned = origin.strip().strip('"').strip("'")

            if cleaned:
                origins.append(cleaned)

        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
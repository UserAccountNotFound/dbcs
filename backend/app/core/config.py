import json
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Digital Bussines Card Service API"
    app_version: str = "1.2.0"
    environment: str = "development"
    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    database_url: str
    secret_key: str

    allowed_origins: str = ""

    public_base_url: str = "http://localhost:5173"

    uploads_dir: Path = Path("/var/lib/dbcs/uploads")
    max_upload_size_mb: int = 5
    templates_css_dir: Path = Path("/opt/dbcs/backend/templates/css")
    
    docs_enabled: bool = True
    redoc_enabled: bool = True

    db_echo: bool = False

    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    self_registration_enabled: bool = False

    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def normalize_allowed_origins(cls, value: object) -> str:
        if value is None:
            return ""

        return str(value)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")

        return value

    @field_validator("refresh_cookie_samesite", mode="before")
    @classmethod
    def normalize_refresh_cookie_samesite(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()

        return value

    @model_validator(mode="after")
    def validate_cookie_security(self) -> "Settings":
        if self.refresh_cookie_samesite == "none" and not self.refresh_cookie_secure:
            raise ValueError(
                "REFRESH_COOKIE_SECURE must be true when REFRESH_COOKIE_SAMESITE is none."
            )

        if (
            self.environment.lower() not in {"development", "dev", "test"}
            and not self.refresh_cookie_secure
        ):
            raise ValueError(
                "REFRESH_COOKIE_SECURE must be true outside development."
            )

        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        raw_value = self.allowed_origins.strip()

        if not raw_value:
            return []

        # Поддерживаем вариант JSON-массива:
        # ALLOWED_ORIGINS=["http://localhost:5173"]
        if raw_value.startswith("["):
            try:
                parsed_value = json.loads(raw_value)

                if isinstance(parsed_value, list):
                    return [
                        str(origin).strip()
                        for origin in parsed_value
                        if str(origin).strip()
                    ]
            except json.JSONDecodeError:
                pass

        # Основной вариант: через запятую.
        return [
            origin.strip()
            for origin in raw_value.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
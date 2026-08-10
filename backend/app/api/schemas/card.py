import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)

from app.core.config import settings


PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-().]{7,64}$")

MESSENGER_FIELDS = (
    "telegram",
    "whatsapp",
    "viber",
    "wechat",
    "messenger_max",
    "discord",
    "vk",
)


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return value


def _validate_phone_value(value: str | None) -> str | None:
    value = _normalize_optional_string(value)
    if value is None:
        return None
    if not PHONE_PATTERN.fullmatch(value):
        raise ValueError("Invalid phone number format.")
    return value


def _validate_messenger_value(value: str | None) -> str | None:
    return _normalize_optional_string(value)


def _validate_website_value(value: str | None) -> str | None:
    value = _normalize_optional_string(value)
    if value is None:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Website must use http or https scheme.")
    if not parsed.netloc:
        raise ValueError("Website must contain a valid domain.")
    return value


class CardTheme(BaseModel):
    color_scheme: Literal["light", "dark"] = "light"
    layout: Literal["classic", "modern", "compact", "corporate", "creative"] = "classic"
    font: Literal["inter", "roboto", "open_sans"] = "inter"
    accent_color: str = Field(
        default="#0f766e",
        pattern=r"^#[0-9a-fA-F]{6}$",
    )
    show_photo: bool = True
    show_qr: bool = True


class CardBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)

    job_title: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)

    phone: str | None = Field(default=None, max_length=64)
    phone_additional: str | None = Field(default=None, max_length=64)
    telegram: str | None = Field(default=None, max_length=255)
    whatsapp: str | None = Field(default=None, max_length=255)
    viber: str | None = Field(default=None, max_length=255)
    wechat: str | None = Field(default=None, max_length=255)
    messenger_max: str | None = Field(default=None, max_length=255)
    discord: str | None = Field(default=None, max_length=255)
    vk: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=2048)
    address: str | None = Field(default=None, max_length=512)
    note: str | None = Field(default=None, max_length=5000)

    template_id: str | None = None
    theme: CardTheme = Field(default_factory=CardTheme)

    avatar_file_id: str | None = None
    logo_file_id: str | None = None

    @field_validator("title", "full_name")
    @classmethod
    def validate_required_text_fields(cls, value: str) -> str:
        normalized = _normalize_optional_string(value)
        if normalized is None:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("job_title", "department", "company", "address", "note")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("phone", "phone_additional")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return _validate_phone_value(value)

    @field_validator(*MESSENGER_FIELDS)
    @classmethod
    def validate_messengers(cls, value: str | None) -> str | None:
        return _validate_messenger_value(value)

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        return _validate_website_value(value)


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)

    job_title: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)

    phone: str | None = Field(default=None, max_length=64)
    phone_additional: str | None = Field(default=None, max_length=64)
    telegram: str | None = Field(default=None, max_length=255)
    whatsapp: str | None = Field(default=None, max_length=255)
    viber: str | None = Field(default=None, max_length=255)
    wechat: str | None = Field(default=None, max_length=255)
    messenger_max: str | None = Field(default=None, max_length=255)
    discord: str | None = Field(default=None, max_length=255)
    vk: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=2048)
    address: str | None = Field(default=None, max_length=512)
    note: str | None = Field(default=None, max_length=5000)

    template_id: str | None = None
    theme: CardTheme | None = None
    is_active: bool | None = None

    avatar_file_id: str | None = None
    logo_file_id: str | None = None

    @field_validator("title", "full_name")
    @classmethod
    def validate_required_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = _normalize_optional_string(value)
        if normalized is None:
            raise ValueError("Field cannot be empty.")
        return normalized

    @field_validator("job_title", "department", "company", "address", "note")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("phone", "phone_additional")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return _validate_phone_value(value)

    @field_validator(*MESSENGER_FIELDS)
    @classmethod
    def validate_messengers(cls, value: str | None) -> str | None:
        return _validate_messenger_value(value)

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        return _validate_website_value(value)


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str

    title: str
    full_name: str

    job_title: str | None
    department: str | None
    company: str | None

    phone: str | None
    phone_additional: str | None
    telegram: str | None
    whatsapp: str | None
    viber: str | None
    wechat: str | None
    messenger_max: str | None
    discord: str | None
    vk: str | None
    email: EmailStr | None
    website: str | None
    address: str | None
    note: str | None

    theme: CardTheme

    template_id: str | None

    avatar_file_id: str | None = None
    logo_file_id: str | None = None

    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def public_url(self) -> str:
        base_url = settings.public_base_url.rstrip("/")
        return f"{base_url}/public/card/{self.slug}"


class CardListResponse(BaseModel):
    items: list[CardResponse]
    total: int
    limit: int
    offset: int
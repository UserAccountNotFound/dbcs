from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TemplateSchema(BaseModel):
    """Структура дизайна шаблона (хранится в schema_json)."""
    
    # Цвета по умолчанию
    primary_color: str = Field(default="#0f766e", pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str = Field(default="#f3f4f6", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#111827", pattern=r"^#[0-9a-fA-F]{6}$")
    
    # Шрифты
    heading_font: str = Field(default="inter", pattern=r"^[a-z_]+$")
    body_font: str = Field(default="inter", pattern=r"^[a-z_]+$")
    
    # Layout
    layout_type: str = Field(default="classic")  # classic, modern, compact, corporate, creative
    show_photo: bool = True
    show_qr: bool = True
    show_logo: bool = False
    photo_position: str = Field(default="left")  # left, top, right
    
    # Декорации
    border_radius: int = Field(default=16, ge=0, le=50)
    shadow: bool = True
    gradient_header: bool = False
    
    @field_validator("layout_type")
    @classmethod
    def validate_layout_type(cls, v: str) -> str:
        allowed = {"classic", "modern", "compact", "corporate", "creative"}
        if v not in allowed:
            raise ValueError(f"layout_type must be one of: {', '.join(allowed)}")
        return v
    
    @field_validator("photo_position")
    @classmethod
    def validate_photo_position(cls, v: str) -> str:
        allowed = {"left", "top", "right"}
        if v not in allowed:
            raise ValueError(f"photo_position must be one of: {', '.join(allowed)}")
        return v


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: str | None
    preview_image: str | None
    is_active: bool
    created_at: datetime

    # schema_json преобразуем в TemplateSchema
    schema_data: TemplateSchema | None = None


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int


class TemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    preview_image: str | None = None
    schema_data: TemplateSchema = Field(default_factory=TemplateSchema)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return v.lower().strip()


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    preview_image: str | None = None
    schema_data: TemplateSchema | None = None
    is_active: bool | None = None


class AdminTemplateResponse(TemplateResponse):
    """Расширенный ответ для админки."""
    updated_at: datetime
    cards_count: int = 0
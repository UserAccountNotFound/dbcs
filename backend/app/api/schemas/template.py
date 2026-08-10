from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TemplateMeta(BaseModel):
    """Лёгкие метаданные шаблона (schema_json). Визуал — в CSS на диске."""

    version: int = 2
    # Опциональный эффект рендерера (например polygon-canvas для Aurora)
    effect: str | None = Field(default=None, max_length=64)
    default_accent: str | None = Field(
        default=None,
        pattern=r"^#[0-9a-fA-F]{6}$",
    )
    default_scheme: str | None = Field(default=None)

    @field_validator("default_scheme")
    @classmethod
    def validate_scheme(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v not in {"light", "dark"}:
            raise ValueError("default_scheme must be light or dark")
        return v

    @field_validator("effect")
    @classmethod
    def validate_effect(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        allowed = {"polygon"}
        if v not in allowed:
            raise ValueError(f"effect must be one of: {', '.join(sorted(allowed))}")
        return v


# Обратная совместимость имени
TemplateSchema = TemplateMeta


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: str | None
    preview_image: str | None
    is_active: bool
    created_at: datetime
    css_url: str | None = None
    has_css: bool = False
    meta: TemplateMeta | None = None
    # deprecated alias для старых клиентов
    schema_data: TemplateMeta | None = None


class TemplateListResponse(BaseModel):
    items: list[TemplateResponse]
    total: int


class TemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    preview_image: str | None = None
    meta: TemplateMeta = Field(default_factory=TemplateMeta)
    schema_data: TemplateMeta | None = None  # alias
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        return v.lower().strip()

    def resolved_meta(self) -> TemplateMeta:
        return self.schema_data or self.meta


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    preview_image: str | None = None
    meta: TemplateMeta | None = None
    schema_data: TemplateMeta | None = None
    is_active: bool | None = None

    def resolved_meta(self) -> TemplateMeta | None:
        if self.schema_data is not None:
            return self.schema_data
        return self.meta


class AdminTemplateResponse(TemplateResponse):
    """Расширенный ответ для админки."""

    updated_at: datetime
    cards_count: int = 0

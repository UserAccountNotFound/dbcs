from pydantic import BaseModel, EmailStr

from app.api.schemas.card import CardTheme
from app.api.schemas.template import TemplateSchema
from app.core.config import settings
from app.core.urls import get_public_card_url
from app.models import Card


class PublicCardResponse(BaseModel):
    slug: str
    title: str
    full_name: str
    job_title: str | None
    department: str | None
    company: str | None
    phone: str | None
    email: EmailStr | None
    website: str | None
    address: str | None
    note: str | None
    
    theme: CardTheme
    template_code: str | None
    
    # НОВОЕ: схема шаблона для рендера
    template_schema: TemplateSchema | None = None
    
    # НОВОЕ: URL изображений
    avatar_url: str | None = None
    logo_url: str | None = None
    
    public_url: str


def build_public_card_response(card: Card) -> PublicCardResponse:
    """Собирает response для публичной визитки."""
    
    # Парсим схему шаблона
    template_schema = None
    if card.template and card.template.schema_json:
        try:
            template_schema = TemplateSchema.model_validate(card.template.schema_json)
        except Exception:
            template_schema = None
    
    # URL аватара и логотипа (публичные endpoints)
    avatar_url = None
    if card.avatar_file_id:
        avatar_url = f"{settings.api_v1_prefix}/public/cards/{card.slug}/avatar"
    
    logo_url = None
    if card.logo_file_id:
        logo_url = f"{settings.api_v1_prefix}/public/cards/{card.slug}/logo"
    
    return PublicCardResponse(
        slug=card.slug,
        title=card.title,
        full_name=card.full_name,
        job_title=card.job_title,
        department=card.department,
        company=card.company,
        phone=card.phone,
        email=card.email,
        website=card.website,
        address=card.address,
        note=card.note,
        theme=CardTheme.model_validate(card.theme),
        template_code=card.template.code if card.template else None,
        template_schema=template_schema,
        avatar_url=avatar_url,
        logo_url=logo_url,
        public_url=get_public_card_url(card.slug),
    )
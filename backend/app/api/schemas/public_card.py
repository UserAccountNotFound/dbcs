from pydantic import BaseModel, EmailStr

from app.api.schemas.card import CardTheme
from app.api.schemas.template import TemplateMeta
from app.core.config import settings
from app.core.urls import get_public_card_url
from app.models import Card
from app.services import css_template_service


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
    template_code: str | None = None
    css_url: str | None = None
    template_effect: str | None = None

    avatar_url: str | None = None
    logo_url: str | None = None

    public_url: str


def build_public_card_response(card: Card) -> PublicCardResponse:
    """Собирает response для публичной визитки."""

    template_code = card.template.code if card.template else None
    css_url = None
    template_effect = None

    if card.template:
        if css_template_service.template_css_exists(card.template.code):
            css_url = css_template_service.css_url_for_code(card.template.code)
        try:
            meta = TemplateMeta.model_validate(card.template.schema_json or {})
            template_effect = meta.effect
        except Exception:
            template_effect = None

    avatar_url = None
    if card.avatar_file_id:
        avatar_url = f"{settings.api_v1_prefix}/public/cards/{card.slug}/avatar"

    logo_url = None
    if card.logo_file_id:
        logo_url = f"{settings.api_v1_prefix}/public/cards/{card.slug}/logo"

    try:
        theme = CardTheme.model_validate(card.theme or {})
    except Exception:
        theme = CardTheme()

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
        theme=theme,
        template_code=template_code,
        css_url=css_url,
        template_effect=template_effect,
        avatar_url=avatar_url,
        logo_url=logo_url,
        public_url=get_public_card_url(card.slug),
    )

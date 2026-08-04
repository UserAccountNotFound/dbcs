from pydantic import BaseModel, EmailStr

from app.api.schemas.card import CardTheme
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

    public_url: str


def build_public_card_response(card: Card) -> PublicCardResponse:
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
        theme=CardTheme.model_validate(card.theme_json),
        template_code=card.template.code if card.template else None,
        public_url=get_public_card_url(card.slug),
    )
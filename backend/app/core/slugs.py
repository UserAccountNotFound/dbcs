import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card
from app.services.exceptions import SlugGenerationError


SLUG_TOKEN_BYTES = 9
MAX_SLUG_ATTEMPTS = 10


def generate_slug() -> str:
    """
    Генерирует криптографически случайный URL-safe slug.

    token_urlsafe(9) обычно дает строку длиной около 12 символов.
    Этого достаточно для публичных ссылок и защиты от перебора.
    """
    return secrets.token_urlsafe(SLUG_TOKEN_BYTES)


def generate_unique_slug(db: Session) -> str:
    for _ in range(MAX_SLUG_ATTEMPTS):
        slug = generate_slug()

        exists = db.scalar(
            select(Card.id)
            .where(Card.slug == slug)
            .limit(1)
        )

        if not exists:
            return slug

    raise SlugGenerationError("Unable to generate unique slug.")
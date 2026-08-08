from app.core.config import settings


def get_public_card_url(slug: str) -> str:
    base_url = settings.public_base_url.rstrip("/")
    return f"{base_url}/public/card/{slug}"
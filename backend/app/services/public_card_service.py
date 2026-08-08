import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_pii
from app.core.utils import get_client_ip, get_user_agent
from app.models import Card, CardVisit
from app.services.exceptions import CardNotFoundError


SOURCE_CARD_VIEW = "card_view"
SOURCE_VCARD_DOWNLOAD = "vcard_download"

# Регулярки для классификации устройств
_MOBILE_RE = re.compile(r"Mobile|Android|iPhone|iPod", re.I)
_TABLET_RE = re.compile(r"iPad|Tablet|Android(?!.*Mobile)", re.I)


def _classify_device(user_agent: str | None) -> str:
    """Классифицирует устройство по User-Agent ДО хеширования."""
    if not user_agent:
        return "Unknown"
    if _TABLET_RE.search(user_agent):
        return "Tablet"
    if _MOBILE_RE.search(user_agent):
        return "Mobile"
    return "Desktop"


def get_active_public_card(db: Session, slug: str) -> Card:
    """Получает активную публичную визитку по slug с подгрузкой связей."""
    card = db.scalar(
        select(Card)
        .options(
            joinedload(Card.template),
            joinedload(Card.avatar_file),
            joinedload(Card.logo_file),
        )
        .where(
            Card.slug == slug,
            Card.is_active.is_(True),
            Card.deleted_at.is_(None),
        )
    )

    if card is None:
        raise CardNotFoundError("Public card not found.")

    return card


def record_visit(
    db: Session,
    card_id: str,
    ip: str | None,
    user_agent: str | None,
    referer: str | None,
    source: str,
) -> CardVisit:
    """Записывает факт посещения визитки с классификацией устройства."""
    device_type = _classify_device(user_agent)

    visit = CardVisit(
        card_id=card_id,
        visited_at=datetime.now(timezone.utc),
        ip_hash=hash_pii(ip) if ip else None,
        user_agent_hash=hash_pii(user_agent) if user_agent else None,
        referer=referer[:2048] if referer else None,
        source=source,
        device_type=device_type,
    )

    db.add(visit)
    db.commit()
    return visit
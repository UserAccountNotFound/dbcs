from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_pii
from app.core.utils import get_client_ip, get_user_agent
from app.models import Card, CardVisit
from app.services.exceptions import CardNotFoundError


SOURCE_CARD_VIEW = "card_view"
SOURCE_VCARD_DOWNLOAD = "vcard_download"


def get_active_public_card(db: Session, slug: str) -> Card:
    card = db.scalar(
        select(Card)
        .options(joinedload(Card.template))
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
    card: Card,
    request: Request,
    source: str,
) -> None:
    referer = request.headers.get("referer")

    if referer and len(referer) > 2048:
        referer = referer[:2048]

    visit = CardVisit(
        card_id=card.id,
        ip_hash=hash_pii(get_client_ip(request)),
        user_agent_hash=hash_pii(get_user_agent(request)),
        referer=referer,
        source=source,
    )

    db.add(visit)
    db.commit()
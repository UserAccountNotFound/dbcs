from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.card import CardCreate, CardTheme, CardUpdate
from app.core.slugs import generate_unique_slug
from app.db.base import utcnow
from app.models import Card, CardTemplate, User, File
from app.services.exceptions import (
    CardNotFoundError,
    TemplateNotFoundError,
    InvalidFileError,
)


def _get_owned_active_card(
    db: Session,
    user_id: str,
    card_id: str,
) -> Card:
    card = db.scalar(
        select(Card).where(
            Card.id == card_id,
            Card.user_id == user_id,
            Card.deleted_at.is_(None),
        )
    )

    if card is None:
        raise CardNotFoundError("Card not found.")

    return card


def _ensure_template_exists_and_active(
    db: Session,
    template_id: str | None,
) -> None:
    if template_id is None:
        return

    template = db.scalar(
        select(CardTemplate).where(
            CardTemplate.id == template_id,
            CardTemplate.is_active.is_(True),
        )
    )

    if template is None:
        raise TemplateNotFoundError("Card template not found or inactive.")


def create_card(
    db: Session,
    user: User,
    payload: CardCreate,
) -> Card:
    _ensure_template_exists_and_active(db, payload.template_id)

    # Проверяем, что файлы принадлежат пользователю
    if payload.avatar_file_id:
        file = db.get(File, payload.avatar_file_id)
        if not file or file.owner_user_id != user.id:
            raise InvalidFileError("Avatar file not found or not owned by user.")
    
    if payload.logo_file_id:
        file = db.get(File, payload.logo_file_id)
        if not file or file.owner_user_id != user.id:
            raise InvalidFileError("Logo file not found or not owned by user.")

    card = Card(
        user_id=user.id,
        slug=generate_unique_slug(db),
        template_id=payload.template_id,
        avatar_file_id=payload.avatar_file_id,
        logo_file_id=payload.logo_file_id,
        title=payload.title,
        full_name=payload.full_name,
        job_title=payload.job_title,
        department=payload.department,
        company=payload.company,
        phone=payload.phone,
        email=payload.email,
        website=payload.website,
        address=payload.address,
        note=payload.note,
        theme=payload.theme.model_dump(),
        is_active=True,
    )

    db.add(card)
    db.commit()
    db.refresh(card)

    return card


def list_cards(
    db: Session,
    user: User,
    limit: int,
    offset: int,
) -> tuple[list[Card], int]:
    cards_query = (
        select(Card)
        .where(
            Card.user_id == user.id,
            Card.deleted_at.is_(None),
        )
        .order_by(Card.created_at.desc(), Card.id.desc())
    )

    count_query = select(func.count()).select_from(cards_query.subquery())
    total = db.scalar(count_query) or 0

    cards = db.scalars(
        cards_query
        .limit(limit)
        .offset(offset)
    ).all()

    return cards, total


def get_card(
    db: Session,
    user: User,
    card_id: str,
) -> Card:
    return _get_owned_active_card(db, user.id, card_id)


def update_card(
    db: Session,
    user: User,
    card_id: str,
    payload: CardUpdate,
) -> Card:
    card = _get_owned_active_card(db, user.id, card_id)

    update_data = payload.model_dump(exclude_unset=True)

    if "template_id" in update_data:
        template_id = update_data.pop("template_id")
        _ensure_template_exists_and_active(db, template_id)
        card.template_id = template_id

    # Обработка файлов
    if "avatar_file_id" in update_data:
        avatar_file_id = update_data.pop("avatar_file_id")
        if avatar_file_id:
            file = db.get(File, avatar_file_id)
            if not file or file.owner_user_id != user.id:
                raise InvalidFileError("Avatar file not found or not owned by user.")
        card.avatar_file_id = avatar_file_id

    if "logo_file_id" in update_data:
        logo_file_id = update_data.pop("logo_file_id")
        if logo_file_id:
            file = db.get(File, logo_file_id)
            if not file or file.owner_user_id != user.id:
                raise InvalidFileError("Logo file not found or not owned by user.")
        card.logo_file_id = logo_file_id

    if "theme" in update_data:
        update_data.pop("theme")

        if payload.theme is not None:
            card.theme = payload.theme.model_dump()
        else:
            card.theme = CardTheme().model_dump()

    for field_name, value in update_data.items():
        setattr(card, field_name, value)

    db.commit()
    db.refresh(card)

    return card


def soft_delete_card(
    db: Session,
    user: User,
    card_id: str,
) -> None:
    card = _get_owned_active_card(db, user.id, card_id)

    card.deleted_at = utcnow()
    card.is_active = False

    db.commit()


def regenerate_card_slug(
    db: Session,
    user: User,
    card_id: str,
) -> Card:
    card = _get_owned_active_card(db, user.id, card_id)

    card.slug = generate_unique_slug(db)

    db.commit()
    db.refresh(card)

    return card
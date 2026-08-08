from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.template import TemplateCreate, TemplateUpdate
from app.models import Card, CardTemplate
from app.services.exceptions import ServiceError


class TemplateError(ServiceError):
    pass


def get_active_templates(db: Session) -> list[CardTemplate]:
    """Список активных шаблонов для пользователей."""
    return list(
        db.scalars(
            select(CardTemplate)
            .where(CardTemplate.is_active.is_(True))
            .order_by(CardTemplate.created_at.asc())
        ).all()
    )


def get_template(db: Session, template_id: str) -> CardTemplate:
    template = db.get(CardTemplate, template_id)
    if not template:
        raise TemplateError("Шаблон не найден.")
    return template


def get_admin_templates(
    db: Session,
    limit: int,
    offset: int,
    search: str | None = None,
) -> tuple[list[tuple[CardTemplate, int]], int]:
    """Список всех шаблонов для админки с количеством использующих их визиток."""
    
    cards_count_subq = (
        select(
            Card.template_id,
            func.count(Card.id).label("cards_count")
        )
        .where(Card.deleted_at.is_(None))
        .group_by(Card.template_id)
        .subquery()
    )

    query = (
        select(CardTemplate, func.coalesce(cards_count_subq.c.cards_count, 0))
        .outerjoin(cards_count_subq, CardTemplate.id == cards_count_subq.c.template_id)
    )

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            CardTemplate.name.ilike(search_filter) | 
            CardTemplate.code.ilike(search_filter)
        )

    count_query = select(func.count(CardTemplate.id))
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.where(
            CardTemplate.name.ilike(search_filter) | 
            CardTemplate.code.ilike(search_filter)
        )

    total = db.scalar(count_query) or 0

    results = db.execute(
        query
        .order_by(CardTemplate.created_at.asc())
        .limit(limit)
        .offset(offset)
    ).all()

    return results, total


def create_template(db: Session, payload: TemplateCreate) -> CardTemplate:
    # Проверка уникальности code
    existing = db.scalar(
        select(CardTemplate).where(CardTemplate.code == payload.code)
    )
    if existing:
        raise TemplateError(f"Шаблон с кодом '{payload.code}' уже существует.")

    template = CardTemplate(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        preview_image=payload.preview_image,
        schema_json=payload.schema_data.model_dump(),
        is_active=payload.is_active,
    )

    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session,
    template_id: str,
    payload: TemplateUpdate,
) -> CardTemplate:
    template = get_template(db, template_id)

    update_data = payload.model_dump(exclude_unset=True)

    if "schema_data" in update_data:
        schema_data = update_data.pop("schema_data")
        if schema_data is not None:
            template.schema_json = schema_data

    for field_name, value in update_data.items():
        setattr(template, field_name, value)

    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: str) -> None:
    """Удаление шаблона. Запрещено, если есть визитки, использующие его."""
    template = get_template(db, template_id)

    cards_count = db.scalar(
        select(func.count(Card.id))
        .where(Card.template_id == template_id, Card.deleted_at.is_(None))
    ) or 0

    if cards_count > 0:
        raise TemplateError(
            f"Нельзя удалить шаблон: его используют {cards_count} визиток. "
            f"Сначала деактивируйте шаблон."
        )

    db.delete(template)
    db.commit()


def toggle_template_active(db: Session, template_id: str) -> CardTemplate:
    template = get_template(db, template_id)
    template.is_active = not template.is_active
    db.commit()
    db.refresh(template)
    return template
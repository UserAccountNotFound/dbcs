from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.api.schemas.admin import AdminUserCreate, AdminUserUpdate
from app.models import User, Card, CardVisit, AuditLog, UserRole
from app.services.exceptions import ServiceError
from app.services.public_card_service import SOURCE_CARD_VIEW, SOURCE_VCARD_DOWNLOAD

from app.core.security import hash_password
from app.db.base import utcnow

class AdminError(ServiceError):
    pass

def create_user(
    db: Session,
    payload: "AdminUserCreate",  # type: ignore
) -> User:
    # Проверяем, не занят ли email активным пользователем
    existing = db.scalar(
        select(User).where(
            User.email == payload.email,
            User.deleted_at.is_(None),
        )
    )
    if existing:
        raise AdminError("Пользователь с таким email уже существует.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, admin: User, user_id: str) -> None:
    if admin.id == user_id:
        raise AdminError("Нельзя удалить самого себя.")

    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise AdminError("Пользователь не найден.")

    user.deleted_at = utcnow()
    user.is_active = False
    db.commit()

def get_users(
    db: Session,
    limit: int,
    offset: int,
    search: str | None = None,
) -> tuple[list[User], int]:
    query = select(User).where(User.deleted_at.is_(None))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_filter),
                User.full_name.ilike(search_filter),
            )
        )

    # Подсчет количества карточек для каждого пользователя
    cards_count_subq = (
        select(
            Card.user_id,
            func.count(Card.id).label("cards_count")
        )
        .where(Card.deleted_at.is_(None))
        .group_by(Card.user_id)
        .subquery()
    )

    query = (
        query
        .outerjoin(cards_count_subq, User.id == cards_count_subq.c.user_id)
        .add_columns(cards_count_subq.c.cards_count)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    results = db.execute(query).all()
    
    users = []
    for row in results:
        user = row[0]
        user.cards_count = row[1] or 0  # type: ignore
        users.append(user)

    count_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.where(
            or_(
                User.email.ilike(search_filter),
                User.full_name.ilike(search_filter),
            )
        )
    
    total = db.scalar(count_query) or 0

    return users, total


def update_user(
    db: Session,
    admin: User,
    user_id: str,
    payload: AdminUserUpdate,
) -> User:
    if admin.id == user_id:
        if payload.is_active is False:
            raise AdminError("Нельзя деактивировать самого себя.")
        if payload.role is not None and payload.role != admin.role:
            raise AdminError("Нельзя изменить собственную роль.")

    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise AdminError("Пользователь не найден.")

    # Проверка email на уникальность, если он меняется
    if payload.email is not None and payload.email != user.email:
        existing = db.scalar(
            select(User).where(
                User.email == payload.email,
                User.deleted_at.is_(None),
            )
        )
        if existing:
            raise AdminError("Этот email уже занят другим пользователем.")
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    if payload.is_active is not None:
        user.is_active = payload.is_active
    
    if payload.role is not None:
        if payload.role == UserRole.SUPERADMIN and admin.role != UserRole.SUPERADMIN:
            raise AdminError("Недостаточно прав для назначения роли SUPERADMIN.")
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return user


def get_cards(
    db: Session,
    limit: int,
    offset: int,
    search: str | None = None,
) -> tuple[list, int]:
    
    visits_count_subq = (
        select(
            CardVisit.card_id,
            func.count(CardVisit.id).label("visits_count")
        )
        .group_by(CardVisit.card_id)
        .subquery()
    )

    query = (
        select(Card, User.email, visits_count_subq.c.visits_count)
        .join(User, Card.user_id == User.id)
        .outerjoin(visits_count_subq, Card.id == visits_count_subq.c.card_id)
        .where(Card.deleted_at.is_(None))
    )

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                Card.title.ilike(search_filter),
                Card.full_name.ilike(search_filter),
                Card.slug.ilike(search_filter),
                User.email.ilike(search_filter),
            )
        )

    count_query = select(func.count(Card.id)).where(Card.deleted_at.is_(None))
    if search:
        search_filter = f"%{search}%"
        count_query = count_query.where(
            or_(
                Card.title.ilike(search_filter),
                Card.full_name.ilike(search_filter),
                Card.slug.ilike(search_filter),
            )
        )

    total = db.scalar(count_query) or 0

    results = db.execute(
        query
        .order_by(Card.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    cards_data = []
    for card, user_email, visits_count in results:
        cards_data.append({
            "card": card,
            "user_email": user_email,
            "visits_count": visits_count or 0,
        })

    return cards_data, total


def deactivate_card(db: Session, card_id: str) -> Card:
    card = db.get(Card, card_id)
    if not card:
        raise AdminError("Визитка не найдена.")
    
    card.is_active = False
    db.commit()
    db.refresh(card)
    return card


def get_audit_logs(
    db: Session,
    limit: int,
    offset: int,
    action: str | None = None,
) -> tuple[list, int]:
    query = (
        select(AuditLog, User.email)
        .outerjoin(User, AuditLog.actor_user_id == User.id)
    )

    if action:
        query = query.where(AuditLog.action == action)

    count_query = select(func.count(AuditLog.id))
    if action:
        count_query = count_query.where(AuditLog.action == action)

    total = db.scalar(count_query) or 0

    results = (
        query
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    logs = []
    for log, actor_email in results:
        logs.append({
            "log": log,
            "actor_email": actor_email,
        })

    return logs, total


def get_overview_stats(db: Session) -> dict:
    total_users = db.scalar(select(func.count(User.id))) or 0
    active_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    
    total_cards = db.scalar(select(func.count(Card.id)).where(Card.deleted_at.is_(None))) or 0
    active_cards = db.scalar(
        select(func.count(Card.id))
        .where(Card.deleted_at.is_(None), Card.is_active.is_(True))
    ) or 0
    
    total_visits = db.scalar(
        select(func.count(CardVisit.id))
        .where(CardVisit.source == SOURCE_CARD_VIEW)
    ) or 0
    
    total_vcard_downloads = db.scalar(
        select(func.count(CardVisit.id))
        .where(CardVisit.source == SOURCE_VCARD_DOWNLOAD)
    ) or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_cards": total_cards,
        "active_cards": active_cards,
        "total_visits": total_visits,
        "total_vcard_downloads": total_vcard_downloads,
    }
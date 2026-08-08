import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from app.models import Card, CardVisit, User
from app.services.public_card_service import SOURCE_CARD_VIEW, SOURCE_VCARD_DOWNLOAD

Period = Literal["7d", "30d", "90d"]

PERIOD_DELTA: dict[Period, timedelta] = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}

KNOWN_REFERRERS = {
    "google": "Google",
    "yandex": "Yandex",
    "bing": "Bing",
    "duckduckgo": "DuckDuckGo",
    "t.me": "Telegram",
    "telegram": "Telegram",
    "facebook": "Facebook",
    "twitter": "Twitter",
    "x.com": "Twitter",
    "linkedin": "LinkedIn",
    "vk.com": "VK",
    "instagram": "Instagram",
    "whatsapp": "WhatsApp",
    "reddit": "Reddit",
}


def _start_of_period(period: Period) -> datetime:
    now = datetime.now(timezone.utc)
    return now - PERIOD_DELTA[period]


def _normalize_referer(referer: str | None) -> str:
    if not referer or referer == "-":
        return "Direct"
    referer = referer.lower()
    for key, label in KNOWN_REFERRERS.items():
        if key in referer:
            return label
    match = re.search(r"https?://([^/]+)", referer)
    if match:
        domain = match.group(1)
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    return "Other"


def get_time_series(db: Session, period: Period) -> list[dict]:
    """Временной ряд: просмотры и скачивания по дням."""
    start_date = _start_of_period(period)

    query = (
        select(
            func.date(CardVisit.visited_at).label("day"),
            func.count(case((CardVisit.source == SOURCE_CARD_VIEW, 1))).label("views"),
            func.count(case((CardVisit.source == SOURCE_VCARD_DOWNLOAD, 1))).label("downloads"),
        )
        .where(CardVisit.visited_at >= start_date)
        .group_by(text("DATE(visited_at)"))
        .order_by(text("DATE(visited_at) ASC"))
    )

    results = db.execute(query).all()
    day_map = {row.day.isoformat(): {"views": row.views, "downloads": row.downloads} for row in results}
    
    series = []
    current = start_date.date()
    end = datetime.now(timezone.utc).date()
    
    while current <= end:
        key = current.isoformat()
        data = day_map.get(key, {"views": 0, "downloads": 0})
        series.append({
            "date": key,
            "views": data["views"],
            "downloads": data["downloads"],
        })
        current += timedelta(days=1)
    
    return series


def get_top_cards(db: Session, period: Period, limit: int = 10) -> list[dict]:
    """Топ-N визиток по просмотрам."""
    start_date = _start_of_period(period)

    query = (
        select(
            Card.id,
            Card.title,
            Card.full_name,
            Card.slug,
            User.email.label("user_email"),
            func.count(case((CardVisit.source == SOURCE_CARD_VIEW, 1))).label("views"),
            func.count(case((CardVisit.source == SOURCE_VCARD_DOWNLOAD, 1))).label("downloads"),
        )
        .join(Card, CardVisit.card_id == Card.id)
        .join(User, Card.user_id == User.id)
        .where(
            CardVisit.visited_at >= start_date,
            Card.deleted_at.is_(None),
        )
        .group_by(Card.id, Card.title, Card.full_name, Card.slug, User.email)
        .order_by(func.count(case((CardVisit.source == SOURCE_CARD_VIEW, 1))).desc())
        .limit(limit)
    )

    results = db.execute(query).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "full_name": row.full_name,
            "slug": row.slug,
            "user_email": row.user_email,
            "views": row.views,
            "downloads": row.downloads,
        }
        for row in results
    ]


def get_top_users(db: Session, period: Period, limit: int = 10) -> list[dict]:
    """Топ-N пользователей по суммарным просмотрам их визиток."""
    start_date = _start_of_period(period)

    query = (
        select(
            User.id,
            User.email,
            User.full_name,
            func.count(Card.id).label("cards_count"),
            func.count(case((CardVisit.source == SOURCE_CARD_VIEW, 1))).label("views"),
            func.count(case((CardVisit.source == SOURCE_VCARD_DOWNLOAD, 1))).label("downloads"),
        )
        .join(Card, Card.user_id == User.id)
        .join(CardVisit, CardVisit.card_id == Card.id, isouter=True)
        .where(
            User.deleted_at.is_(None),
            Card.deleted_at.is_(None),
            (CardVisit.visited_at >= start_date) | (CardVisit.id.is_(None)),
        )
        .group_by(User.id, User.email, User.full_name)
        .order_by(func.count(case((CardVisit.source == SOURCE_CARD_VIEW, 1))).desc())
        .limit(limit)
    )

    results = db.execute(query).all()
    return [
        {
            "id": row.id,
            "email": row.email,
            "full_name": row.full_name,
            "cards_count": row.cards_count,
            "views": row.views,
            "downloads": row.downloads,
        }
        for row in results
    ]


def get_referrers(db: Session, period: Period, limit: int = 10) -> list[dict]:
    """Топ источников трафика."""
    start_date = _start_of_period(period)

    query = (
        select(CardVisit.referer)
        .where(CardVisit.visited_at >= start_date)
    )
    
    all_refs = db.execute(query).scalars().all()
    
    counts: dict[str, int] = {}
    for ref in all_refs:
        key = _normalize_referer(ref)
        counts[key] = counts.get(key, 0) + 1
    
    sorted_refs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"source": name, "count": count} for name, count in sorted_refs]


def get_devices(db: Session, period: Period) -> list[dict]:
    """Распределение по типам устройств (читаем device_type, а не user_agent_hash)."""
    start_date = _start_of_period(period)

    query = (
        select(
            CardVisit.device_type,
            func.count(CardVisit.id).label("count"),
        )
        .where(CardVisit.visited_at >= start_date)
        .group_by(CardVisit.device_type)
    )
    
    results = db.execute(query).all()
    
    # Группируем и нормализуем (Unknown → если device_type пустой)
    counts: dict[str, int] = {}
    for device_type, count in results:
        key = device_type or "Unknown"
        counts[key] = counts.get(key, 0) + count
    
    return [{"device": k, "count": v} for k, v in counts.items() if v > 0]


def get_hourly_heatmap(db: Session, period: Period) -> list[dict]:
    """Активность по дням недели и часам."""
    start_date = _start_of_period(period)

    query = (
        select(
            func.dayofweek(CardVisit.visited_at).label("dow"),
            func.hour(CardVisit.visited_at).label("hour"),
            func.count(CardVisit.id).label("count"),
        )
        .where(CardVisit.visited_at >= start_date)
        .group_by(text("DAYOFWEEK(visited_at)"), text("HOUR(visited_at)"))
    )

    results = db.execute(query).all()
    
    heatmap = []
    for row in results:
        if row.dow == 1:  # Воскресенье
            dow_norm = 6
        else:
            dow_norm = row.dow - 2
        
        heatmap.append({
            "day_of_week": dow_norm,
            "hour": row.hour,
            "count": row.count,
        })
    
    return heatmap


def get_extended_analytics(db: Session, period: Period) -> dict:
    """Собирает всю аналитику в один ответ."""
    return {
        "period": period,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "time_series": get_time_series(db, period),
        "top_cards": get_top_cards(db, period, limit=10),
        "top_users": get_top_users(db, period, limit=10),
        "referrers": get_referrers(db, period, limit=10),
        "devices": get_devices(db, period),
        "hourly_heatmap": get_hourly_heatmap(db, period),
    }
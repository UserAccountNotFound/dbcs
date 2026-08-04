from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.api.schemas.stats import CardStatsResponse, DailyStat
from app.db.base import utcnow
from app.models import Card, CardVisit
from app.services.public_card_service import (
    SOURCE_CARD_VIEW,
    SOURCE_VCARD_DOWNLOAD,
)


def get_card_stats(db: Session, card: Card) -> CardStatsResponse:
    now = utcnow()
    since = now - timedelta(days=30)

    total_views = db.scalar(
        select(func.count(CardVisit.id)).where(
            CardVisit.card_id == card.id,
            CardVisit.source == SOURCE_CARD_VIEW,
        )
    ) or 0

    total_vcard_downloads = db.scalar(
        select(func.count(CardVisit.id)).where(
            CardVisit.card_id == card.id,
            CardVisit.source == SOURCE_VCARD_DOWNLOAD,
        )
    ) or 0

    visit_date = func.date(CardVisit.visited_at)

    daily_query = (
        select(
            visit_date.label("date"),
            func.sum(
                case(
                    (CardVisit.source == SOURCE_CARD_VIEW, 1),
                    else_=0,
                )
            ).label("views"),
            func.sum(
                case(
                    (CardVisit.source == SOURCE_VCARD_DOWNLOAD, 1),
                    else_=0,
                )
            ).label("vcard_downloads"),
        )
        .where(
            CardVisit.card_id == card.id,
            CardVisit.visited_at >= since,
            CardVisit.source.in_(
                [
                    SOURCE_CARD_VIEW,
                    SOURCE_VCARD_DOWNLOAD,
                ]
            ),
        )
        .group_by(visit_date)
        .order_by(visit_date)
    )

    daily_rows = db.execute(daily_query).all()

    daily_map: dict[date, object] = {}

    for row in daily_rows:
        row_date = row.date

        if hasattr(row_date, "date"):
            row_date = row_date.date()

        daily_map[row_date] = row

    daily: list[DailyStat] = []

    views_last_30_days = 0
    vcard_downloads_last_30_days = 0

    for days_ago in range(30, -1, -1):
        current_date = (now - timedelta(days=days_ago)).date()
        row = daily_map.get(current_date)

        views = int(getattr(row, "views", 0) or 0)
        vcard_downloads = int(getattr(row, "vcard_downloads", 0) or 0)

        views_last_30_days += views
        vcard_downloads_last_30_days += vcard_downloads

        daily.append(
            DailyStat(
                date=current_date,
                views=views,
                vcard_downloads=vcard_downloads,
            )
        )

    return CardStatsResponse(
        total_views=int(total_views),
        total_vcard_downloads=int(total_vcard_downloads),
        views_last_30_days=views_last_30_days,
        vcard_downloads_last_30_days=vcard_downloads_last_30_days,
        daily=daily,
    )
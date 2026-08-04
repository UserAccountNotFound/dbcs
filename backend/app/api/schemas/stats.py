from datetime import date

from pydantic import BaseModel


class DailyStat(BaseModel):
    date: date
    views: int
    vcard_downloads: int


class CardStatsResponse(BaseModel):
    total_views: int
    total_vcard_downloads: int

    views_last_30_days: int
    vcard_downloads_last_30_days: int

    daily: list[DailyStat]
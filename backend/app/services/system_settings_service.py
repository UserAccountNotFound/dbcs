"""Системные настройки приложения (документация API и др.)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import utcnow
from app.models.system_settings import SystemSettings
from app.services.exceptions import ServiceError


class SystemSettingsError(ServiceError):
    pass


@dataclass(frozen=True)
class DocsAccessFlags:
    docs_enabled: bool
    redoc_enabled: bool


def get_or_create_settings(db: Session) -> SystemSettings:
    row = db.get(SystemSettings, 1)
    if row is not None:
        return row
    row = SystemSettings(
        id=1,
        docs_enabled=settings.docs_enabled,
        redoc_enabled=settings.redoc_enabled,
        updated_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_docs_flags(db: Session) -> DocsAccessFlags:
    row = get_or_create_settings(db)
    return DocsAccessFlags(
        docs_enabled=row.docs_enabled,
        redoc_enabled=row.redoc_enabled,
    )


def update_docs_settings(
    db: Session,
    *,
    docs_enabled: bool | None = None,
    redoc_enabled: bool | None = None,
) -> SystemSettings:
    row = get_or_create_settings(db)
    if docs_enabled is not None:
        row.docs_enabled = docs_enabled
    if redoc_enabled is not None:
        row.redoc_enabled = redoc_enabled
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row

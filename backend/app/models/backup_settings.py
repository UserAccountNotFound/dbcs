from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class BackupSettings(Base):
    """Синглтон настроек резервного копирования (одна строка, id=1)."""

    __tablename__ = "backup_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="/var/lib/dbcs/backups",
    )

    # Выключено / hourly / daily / weekly
    schedule: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="daily",
    )

    # Для daily/weekly: час UTC 0–23 (в UI задаётся в локальном поясе)
    schedule_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Для weekly: 0=пн … 6=вс (ISO weekday - 1)
    schedule_weekday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    retention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=7)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_backup_file: Mapped[str | None] = mapped_column(String(512), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

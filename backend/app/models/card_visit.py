from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.card import Card


class CardVisit(Base):
    __tablename__ = "card_visits"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    card_id: Mapped[str] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    visited_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        index=True,
    )

    ip_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    referer: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    device_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default="Unknown",
        index=True,
    )
    
    card: Mapped["Card"] = relationship(
        back_populates="visits",
    )
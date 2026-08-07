from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.card_template import CardTemplate
    from app.models.card_visit import CardVisit
    from app.models.user import User
    from app.models.file import File


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("card_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    avatar_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    logo_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    job_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    theme: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    owner: Mapped["User"] = relationship(
        back_populates="cards",
    )

    avatar_file: Mapped[Optional["File"]] = relationship(
        foreign_keys=[avatar_file_id],
    )

    logo_file: Mapped[Optional["File"]] = relationship(
        foreign_keys=[logo_file_id],
    )
    
    template: Mapped[Optional["CardTemplate"]] = relationship(
        back_populates="cards",
    )

    visits: Mapped[list["CardVisit"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
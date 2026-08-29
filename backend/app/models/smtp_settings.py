from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class SmtpSettings(Base):
    """Синглтон SMTP (одна строка, id=1)."""

    __tablename__ = "smtp_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    host: Mapped[str] = mapped_column(String(255), nullable=False, default="smtp.gmail.com")
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)

    # STARTTLS (587) или implicit SSL (465)
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    username: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    password: Mapped[str] = mapped_column(Text, nullable=False, default="")

    from_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="DBCS")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

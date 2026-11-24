"""SQLAlchemy ORM models for shortened URLs and click analytics."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shorty_api.core.database import Base


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class ShortURL(Base):
    """Stores a shortened URL mapping."""

    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    short_code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)

    clicks: Mapped[list["ClickEvent"]] = relationship(
        back_populates="url",
        cascade="all, delete-orphan",
    )


class ClickEvent(Base):
    """Stores an individual redirect click for analytics."""

    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("urls.id", ondelete="CASCADE"), index=True, nullable=False)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    device_type: Mapped[str] = mapped_column(String(32), default="desktop", nullable=False)
    referer: Mapped[str | None] = mapped_column(String(512), nullable=True)

    url: Mapped[ShortURL] = relationship(back_populates="clicks")

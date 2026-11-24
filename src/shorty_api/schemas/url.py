"""Pydantic request and response schemas for the URL shortener API."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    """Payload to create a new short URL."""

    url: HttpUrl = Field(description="URL original válida (debe empezar con http:// o https://).")
    custom_alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alias personalizado opcional (letras, números, '-' o '_').",
    )


class ShortenResponse(BaseModel):
    """Response returned when a short URL is created."""

    short_code: str
    short_url: str
    original_url: str
    created_at: datetime


class ClickStatsResponse(BaseModel):
    """Aggregated analytics for a shortened URL."""

    short_code: str
    original_url: str
    created_at: datetime
    total_clicks: int
    clicks_by_device: dict[str, int]
    top_referers: dict[str, int]
    last_clicked_at: datetime | None

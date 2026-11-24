"""Business logic for URL shortening, click recording, and analytics."""

from collections import Counter
import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from shorty_api.models.url import ClickEvent, ShortURL
from shorty_api.schemas.url import ClickStatsResponse, ShortenRequest

BASE62_ALPHABET = string.ascii_letters + string.digits
RESERVED_CODES = {"health", "docs", "redoc", "openapi.json", "api"}


class AliasConflictError(Exception):
    """Raised when a requested custom alias is already taken."""


class ReservedAliasError(Exception):
    """Raised when a requested custom alias conflicts with API routes."""


def generate_short_code(length: int = 6) -> str:
    """Generate a cryptographically random Base62 short code."""
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def detect_device_type(user_agent: str | None) -> str:
    """Classify a User-Agent string into bot, tablet, mobile, or desktop."""
    if not user_agent:
        return "unknown"
    ua = user_agent.lower()
    if any(token in ua for token in ("bot", "crawler", "spider", "curl", "python-httpx")):
        return "bot"
    if any(token in ua for token in ("ipad", "tablet")):
        return "tablet"
    if any(token in ua for token in ("mobile", "android", "iphone")):
        return "mobile"
    return "desktop"


def _code_exists(db: Session, short_code: str) -> bool:
    stmt = select(ShortURL.id).where(ShortURL.short_code == short_code)
    return db.execute(stmt).scalar_one_or_none() is not None


def _allocate_unique_code(db: Session, length: int = 6, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        candidate = generate_short_code(length)
        if candidate.lower() not in RESERVED_CODES and not _code_exists(db, candidate):
            return candidate
    raise RuntimeError("Could not allocate a unique short code.")


def create_short_url(db: Session, payload: ShortenRequest) -> ShortURL:
    """Create and persist a new ShortURL record."""
    if payload.custom_alias:
        alias = payload.custom_alias
        if alias.lower() in RESERVED_CODES:
            raise ReservedAliasError(f"El alias '{alias}' está reservado por la API.")
        if _code_exists(db, alias):
            raise AliasConflictError(f"El alias '{alias}' ya está en uso.")
        short_code = alias
    else:
        short_code = _allocate_unique_code(db)

    record = ShortURL(
        short_code=short_code,
        original_url=str(payload.url),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_by_code(db: Session, short_code: str) -> ShortURL | None:
    """Look up a ShortURL by its short_code."""
    stmt = select(ShortURL).where(ShortURL.short_code == short_code)
    return db.execute(stmt).scalar_one_or_none()


def record_click(
    db: Session,
    url_record: ShortURL,
    user_agent: str | None,
    referer: str | None,
) -> ClickEvent:
    """Record a redirect click event for analytics."""
    click = ClickEvent(
        url_id=url_record.id,
        user_agent=user_agent[:512] if user_agent else None,
        device_type=detect_device_type(user_agent),
        referer=referer[:512] if referer else None,
    )
    db.add(click)
    db.commit()
    db.refresh(click)
    return click


def get_url_stats(db: Session, short_code: str) -> ClickStatsResponse | None:
    """Aggregate click analytics for a given short_code."""
    url_record = get_by_code(db, short_code)
    if url_record is None:
        return None

    clicks = url_record.clicks
    device_counts = Counter(click.device_type for click in clicks)
    referer_counts = Counter(click.referer or "direct" for click in clicks)
    last_clicked_at = max((click.clicked_at for click in clicks), default=None)

    return ClickStatsResponse(
        short_code=url_record.short_code,
        original_url=url_record.original_url,
        created_at=url_record.created_at,
        total_clicks=len(clicks),
        clicks_by_device=dict(device_counts),
        top_referers=dict(referer_counts.most_common(5)),
        last_clicked_at=last_clicked_at,
    )

"""HTTP routes for creating short URLs, redirecting, and querying analytics."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from shorty_api.core.config import settings
from shorty_api.core.database import get_db
from shorty_api.schemas.url import ClickStatsResponse, ShortenRequest, ShortenResponse
from shorty_api.services.url_service import (
    AliasConflictError,
    ReservedAliasError,
    create_short_url,
    get_by_code,
    get_url_stats,
    record_click,
)

router = APIRouter()


@router.post(
    "/api/v1/shorten",
    response_model=ShortenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["urls"],
)
def shorten_url(
    payload: ShortenRequest,
    db: Session = Depends(get_db),
) -> ShortenResponse:
    """Crea un nuevo enlace corto (con código aleatorio o alias personalizado)."""
    try:
        record = create_short_url(db, payload)
    except ReservedAliasError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AliasConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    base = settings.base_url.rstrip("/")
    return ShortenResponse(
        short_code=record.short_code,
        short_url=f"{base}/{record.short_code}",
        original_url=record.original_url,
        created_at=record.created_at,
    )


@router.get(
    "/api/v1/stats/{short_code}",
    response_model=ClickStatsResponse,
    tags=["analytics"],
)
def read_url_stats(
    short_code: str,
    db: Session = Depends(get_db),
) -> ClickStatsResponse:
    """Devuelve las analíticas de clics para un enlace corto."""
    stats = get_url_stats(db, short_code)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el enlace '{short_code}'.",
        )
    return stats


@router.get("/{short_code}", tags=["redirect"])
def redirect_to_original(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Redirige al enlace original (HTTP 307) y registra el clic."""
    record = get_by_code(db, short_code)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el enlace '{short_code}'.",
        )

    record_click(
        db=db,
        url_record=record,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )
    return RedirectResponse(
        url=record.original_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )

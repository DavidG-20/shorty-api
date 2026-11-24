"""FastAPI application entry point."""

from fastapi import FastAPI

from shorty_api import __version__
from shorty_api.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="API REST de acortador de URLs con analíticas de clics y rate limiting.",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic health endpoint to verify the service is running."""
    return {"status": "ok", "service": settings.app_name, "version": __version__}

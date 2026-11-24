"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from shorty_api import __version__
from shorty_api.core.config import settings
from shorty_api.core.database import Base, engine
from shorty_api.models import url as _url_models  # noqa: F401
from shorty_api.routers.urls import router as urls_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize database tables on application startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="API REST de acortador de URLs con analíticas de clics y rate limiting.",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Attach baseline HTTP security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Endpoint de salud para comprobar que el servicio está activo."""
    return {"status": "ok", "service": settings.app_name, "version": __version__}


app.include_router(urls_router)

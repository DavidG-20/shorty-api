"""Shared pytest fixtures with an isolated in-memory SQLite database."""

from collections.abc import Generator

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from shorty_api.core.database import Base, get_db
from shorty_api.main import app
from shorty_api.services.rate_limiter import rate_limiter


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient backed by a fresh in-memory SQLite DB."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.testing = True
    rate_limiter.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.state.testing = False
    app.dependency_overrides.clear()
    rate_limiter.reset()
    Base.metadata.drop_all(bind=engine)

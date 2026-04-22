import os
from unittest.mock import AsyncMock, patch

import databases
import pytest
import sqlalchemy
from httpx import ASGITransport, AsyncClient

from src.infrastructure.api.dependencies import get_product_repository, get_revoked_token_repository
from src.infrastructure.api.middleware.rate_limit import limiter
from src.infrastructure.database.connection import metadata
from src.infrastructure.database.repositories import ProductRepository, RevokedTokenRepository
from src.infrastructure.database.seed import seed_catalog as real_seed_catalog
from src.main import app

_TEST_DB_FILE = "test_coffee_shop.db"
_TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_TEST_DB_FILE}"


@pytest.fixture
async def test_db():
    """
    Provides a connected test database with all tables created.
    Uses a file-based SQLite DB so that both sqlalchemy (sync, for DDL)
    and databases (async, for queries) share the same storage.
    Cleaned up after each test.
    """
    engine = sqlalchemy.create_engine(
        f"sqlite:///{_TEST_DB_FILE}",
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)

    db = databases.Database(_TEST_DATABASE_URL)
    await db.connect()

    yield db

    await db.disconnect()
    engine.dispose()
    if os.path.exists(_TEST_DB_FILE):
        os.remove(_TEST_DB_FILE)


def _make_client(test_db: databases.Database):
    """
    Returns an async context manager that yields an httpx client bound to the app,
    with repositories overridden to use the test database.
    The app's production lifespan (connect + seed) is patched to a no-op so
    the test database is not polluted by the app startup sequence.
    """
    app.dependency_overrides[get_product_repository] = lambda: ProductRepository(test_db)

    return _ClientContext(test_db)


class _ClientContext:
    def __init__(self, test_db: databases.Database):
        self._test_db = test_db
        self._patches = [
            patch("src.main.database.connect", new_callable=AsyncMock),
            patch("src.main.database.disconnect", new_callable=AsyncMock),
            patch("src.main.seed_catalog", new_callable=AsyncMock),
            patch("src.main.notification_worker", new_callable=AsyncMock),
            patch("src.main.redis_client.aclose", new_callable=AsyncMock),
        ]

    async def __aenter__(self) -> AsyncClient:
        for p in self._patches:
            p.start()
        app.dependency_overrides[get_revoked_token_repository] = lambda: RevokedTokenRepository(self._test_db)
        limiter.enabled = False
        self._http = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        return await self._http.__aenter__()

    async def __aexit__(self, *args):
        await self._http.__aexit__(*args)
        for p in self._patches:
            p.stop()
        limiter.enabled = True
        app.dependency_overrides.clear()


@pytest.fixture
async def client(test_db):
    """HTTP client with an empty test database."""
    async with _make_client(test_db) as c:
        yield c


@pytest.fixture
async def seeded_client(test_db):
    """HTTP client with the catalog pre-seeded into the test database."""
    await real_seed_catalog(test_db)
    async with _make_client(test_db) as c:
        yield c

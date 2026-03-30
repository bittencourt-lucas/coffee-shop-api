import pytest
from httpx import AsyncClient

from tests.integration.conftest import _ClientContext


@pytest.fixture
async def client(test_db):
    async with _ClientContext(test_db) as c:
        yield c


class TestHealthcheck:
    async def test_returns_200(self, client: AsyncClient):
        response = await client.get("/healthcheck")
        assert response.status_code == 200

    async def test_returns_ok_status(self, client: AsyncClient):
        data = (await client.get("/healthcheck")).json()
        assert data == {"status": "ok"}

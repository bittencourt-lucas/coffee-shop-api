from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.core.enums import Role
from src.infrastructure.api.dependencies import (
    get_idempotency_repository,
    get_notification_service,
    get_order_repository,
    get_payment_service,
    get_product_repository,
)
from src.infrastructure.auth.jwt import create_access_token
from src.infrastructure.database.repositories import IdempotencyRepository, OrderRepository, ProductRepository
from src.infrastructure.database.seed import seed_catalog as real_seed_catalog
from src.main import app

from tests.integration.conftest import _ClientContext

_CUSTOMER_ID = uuid4()


def _auth_headers() -> dict:
    token = create_access_token(user_id=_CUSTOMER_ID, role=Role.CUSTOMER)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def idempotency_client(test_db):
    """HTTP client with all dependencies wired to the test DB, payment mocked."""
    await real_seed_catalog(test_db)

    mock_payment = AsyncMock()
    mock_payment.process.return_value = {"id": "pay-123", "status": "approved"}
    mock_notification = AsyncMock()

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_product_repository] = lambda: ProductRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment
    app.dependency_overrides[get_notification_service] = lambda: mock_notification
    app.dependency_overrides[get_idempotency_repository] = lambda: IdempotencyRepository(test_db)

    async with _ClientContext(test_db) as c:
        yield c, mock_payment


async def _get_product_id(client: AsyncClient) -> str:
    menu = (await client.get("/menu")).json()
    return menu[0]["variations"][0]["id"]


class TestIdempotencyKeyDeduplication:
    async def test_second_request_with_same_key_returns_201(self, idempotency_client):
        client, _ = idempotency_client
        product_id = await _get_product_id(client)
        key = str(uuid4())

        await client.post(
            "/orders/", json={"product_ids": [product_id]},
            headers={**_auth_headers(), "Idempotency-Key": key},
        )
        response = await client.post(
            "/orders/", json={"product_ids": [product_id]},
            headers={**_auth_headers(), "Idempotency-Key": key},
        )

        assert response.status_code == 201

    async def test_second_request_returns_identical_order_id(self, idempotency_client):
        client, _ = idempotency_client
        product_id = await _get_product_id(client)
        key = str(uuid4())

        headers = {**_auth_headers(), "Idempotency-Key": key}
        first = (await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)).json()
        second = (await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)).json()

        assert first["id"] == second["id"]

    async def test_duplicate_key_does_not_charge_payment_twice(self, idempotency_client):
        client, mock_payment = idempotency_client
        product_id = await _get_product_id(client)
        key = str(uuid4())

        headers = {**_auth_headers(), "Idempotency-Key": key}
        await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)
        await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)

        mock_payment.process.assert_called_once()

    async def test_different_keys_create_different_orders(self, idempotency_client):
        client, mock_payment = idempotency_client
        product_id = await _get_product_id(client)

        first = (await client.post(
            "/orders/", json={"product_ids": [product_id]},
            headers={**_auth_headers(), "Idempotency-Key": str(uuid4())},
        )).json()
        second = (await client.post(
            "/orders/", json={"product_ids": [product_id]},
            headers={**_auth_headers(), "Idempotency-Key": str(uuid4())},
        )).json()

        assert first["id"] != second["id"]
        assert mock_payment.process.call_count == 2

    async def test_request_without_key_always_creates_new_order(self, idempotency_client):
        client, mock_payment = idempotency_client
        product_id = await _get_product_id(client)

        first = (await client.post(
            "/orders/", json={"product_ids": [product_id]}, headers=_auth_headers()
        )).json()
        second = (await client.post(
            "/orders/", json={"product_ids": [product_id]}, headers=_auth_headers()
        )).json()

        assert first["id"] != second["id"]
        assert mock_payment.process.call_count == 2

    async def test_cached_response_matches_original_fields(self, idempotency_client):
        client, _ = idempotency_client
        product_id = await _get_product_id(client)
        key = str(uuid4())

        headers = {**_auth_headers(), "Idempotency-Key": key}
        first = (await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)).json()
        second = (await client.post("/orders/", json={"product_ids": [product_id]}, headers=headers)).json()

        assert second["status"] == first["status"]
        assert second["total_price"] == first["total_price"]
        assert second["product_ids"] == first["product_ids"]

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.core.exceptions import PaymentFailedError
from src.infrastructure.api.dependencies import get_order_repository, get_payment_service
from src.infrastructure.database.repositories import OrderRepository
from src.main import app

from tests.integration.conftest import _ClientContext


_PRODUCT_IDS = [str(uuid4()), str(uuid4())]
_TOTAL_PRICE = 19.90
_ORDER_PAYLOAD = {"product_ids": _PRODUCT_IDS, "total_price": _TOTAL_PRICE}


@pytest.fixture
async def order_client(test_db):
    """HTTP client with order repository wired to the test DB and a successful payment mock."""
    mock_payment = AsyncMock()
    mock_payment.process.return_value = {"id": "pay-123", "status": "approved"}

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment

    async with _ClientContext(test_db) as c:
        yield c


@pytest.fixture
async def failing_payment_client(test_db):
    """HTTP client where the payment service always raises PaymentFailedError."""
    mock_payment = AsyncMock()
    mock_payment.process.side_effect = PaymentFailedError("payment declined after 3 retries")

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment

    async with _ClientContext(test_db) as c:
        yield c


class TestCreateOrderStatus:
    async def test_returns_201_on_successful_payment(self, order_client: AsyncClient):
        response = await order_client.post("/orders/", json=_ORDER_PAYLOAD)
        assert response.status_code == 201

    async def test_returns_502_when_payment_fails(self, failing_payment_client: AsyncClient):
        response = await failing_payment_client.post("/orders/", json=_ORDER_PAYLOAD)
        assert response.status_code == 502

    async def test_returns_422_on_missing_body(self, order_client: AsyncClient):
        response = await order_client.post("/orders/", json={})
        assert response.status_code == 422


class TestCreateOrderResponse:
    async def test_response_contains_id(self, order_client: AsyncClient):
        data = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()
        assert "id" in data

    async def test_order_status_is_waiting(self, order_client: AsyncClient):
        data = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()
        assert data["status"] == "WAITING"

    async def test_total_price_matches_request(self, order_client: AsyncClient):
        data = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()
        assert data["total_price"] == _TOTAL_PRICE

    async def test_product_ids_match_request(self, order_client: AsyncClient):
        data = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()
        assert set(data["product_ids"]) == set(_PRODUCT_IDS)


class TestCreateOrderPaymentError:
    async def test_error_detail_mentions_payment(self, failing_payment_client: AsyncClient):
        data = (await failing_payment_client.post("/orders/", json=_ORDER_PAYLOAD)).json()
        assert "payment" in data["detail"].lower()

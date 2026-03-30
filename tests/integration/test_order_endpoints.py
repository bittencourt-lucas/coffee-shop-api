from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.core.exceptions import PaymentFailedError
from src.core.enums import OrderStatus
from src.infrastructure.api.dependencies import get_order_repository, get_payment_service, get_notification_service
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

    mock_notification = AsyncMock()

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment
    app.dependency_overrides[get_notification_service] = lambda: mock_notification

    async with _ClientContext(test_db) as c:
        yield c


@pytest.fixture
async def failing_payment_client(test_db):
    """HTTP client where the payment service always raises PaymentFailedError."""
    mock_payment = AsyncMock()
    mock_payment.process.side_effect = PaymentFailedError("payment declined after 3 retries")

    mock_notification = AsyncMock()

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment
    app.dependency_overrides[get_notification_service] = lambda: mock_notification

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


class TestUpdateOrderStatusAccess:
    async def test_returns_403_for_customer_role(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers={"X-Role": "CUSTOMER"},
        )
        assert response.status_code == 403

    async def test_returns_200_for_manager_role(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers={"X-Role": "MANAGER"},
        )
        assert response.status_code == 200


class TestUpdateOrderStatusTransitions:
    async def test_valid_transition_waiting_to_preparation(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        data = (await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers={"X-Role": "MANAGER"},
        )).json()
        assert data["status"] == OrderStatus.PREPARATION.value

    async def test_invalid_transition_waiting_to_ready(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.READY.value},
            headers={"X-Role": "MANAGER"},
        )
        assert response.status_code == 422

    async def test_invalid_transition_waiting_to_delivered(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.DELIVERED.value},
            headers={"X-Role": "MANAGER"},
        )
        assert response.status_code == 422

    async def test_full_transition_chain(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        for new_status in [OrderStatus.PREPARATION, OrderStatus.READY, OrderStatus.DELIVERED]:
            data = (await order_client.patch(
                f"/orders/{order_id}/status",
                json={"status": new_status.value},
                headers={"X-Role": "MANAGER"},
            )).json()
            assert data["status"] == new_status.value

    async def test_returns_404_for_unknown_order(self, order_client: AsyncClient):
        response = await order_client.patch(
            f"/orders/{uuid4()}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers={"X-Role": "MANAGER"},
        )
        assert response.status_code == 404

    async def test_transition_error_detail_message(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        data = (await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.DELIVERED.value},
            headers={"X-Role": "MANAGER"},
        )).json()
        assert "Cannot transition" in data["detail"]


class TestGetOrderDetail:
    async def test_returns_404_for_unknown_order(self, order_client: AsyncClient):
        response = await order_client.get(f"/orders/{uuid4()}")
        assert response.status_code == 404

    async def test_returns_200_for_existing_order(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        response = await order_client.get(f"/orders/{order_id}")
        assert response.status_code == 200

    async def test_response_contains_required_fields(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        data = (await order_client.get(f"/orders/{order_id}")).json()
        assert "id" in data
        assert "status" in data
        assert "total_price" in data
        assert "created_at" in data
        assert "items" in data

    async def test_detail_matches_created_order(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        data = (await order_client.get(f"/orders/{order_id}")).json()
        assert data["id"] == order_id
        assert data["status"] == "WAITING"
        assert data["total_price"] == _TOTAL_PRICE

    async def test_items_list_is_present(self, order_client: AsyncClient):
        order_id = (await order_client.post("/orders/", json=_ORDER_PAYLOAD)).json()["id"]
        data = (await order_client.get(f"/orders/{order_id}")).json()
        assert isinstance(data["items"], list)

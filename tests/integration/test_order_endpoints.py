from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from src.core.enums import OrderStatus, Role
from src.core.exceptions import PaymentFailedError
from src.infrastructure.api.dependencies import (
    get_idempotency_repository,
    get_notification_service,
    get_order_repository,
    get_payment_service,
    get_product_repository,
    get_user_repository,
)
from src.infrastructure.auth.jwt import create_access_token
from src.infrastructure.database.repositories import (
    IdempotencyRepository,
    OrderRepository,
    ProductRepository,
    UserRepository,
)
from src.infrastructure.database.seed import seed_catalog as real_seed_catalog
from src.main import app

from tests.integration.conftest import _ClientContext

_DEFAULT_CUSTOMER_ID = uuid4()
_DEFAULT_MANAGER_ID = uuid4()


def _auth_headers(role: Role, user_id: UUID | None = None) -> dict:
    uid = user_id or (_DEFAULT_CUSTOMER_ID if role == Role.CUSTOMER else _DEFAULT_MANAGER_ID)
    token = create_access_token(user_id=uid, role=role)
    return {"Authorization": f"Bearer {token}"}


async def _get_product_ids(client: AsyncClient, count: int = 2) -> list[str]:
    """Fetch real product IDs from the seeded menu."""
    menu = (await client.get("/menu")).json()
    ids = []
    for item in menu:
        for variation in item["variations"]:
            ids.append(variation["id"])
            if len(ids) == count:
                return ids
    return ids


@pytest.fixture
async def order_client(test_db):
    """HTTP client with catalog seeded and all dependencies wired to the test DB."""
    await real_seed_catalog(test_db)

    mock_payment = AsyncMock()
    mock_payment.process.return_value = {"id": "pay-123", "status": "approved"}
    mock_notification = AsyncMock()

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_product_repository] = lambda: ProductRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment
    app.dependency_overrides[get_notification_service] = lambda: mock_notification
    app.dependency_overrides[get_idempotency_repository] = lambda: IdempotencyRepository(test_db)
    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)

    async with _ClientContext(test_db) as c:
        yield c


@pytest.fixture
async def failing_payment_client(test_db):
    """HTTP client where the payment service always raises PaymentFailedError."""
    await real_seed_catalog(test_db)

    mock_payment = AsyncMock()
    mock_payment.process.side_effect = PaymentFailedError("payment declined after 3 retries")
    mock_notification = AsyncMock()

    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_product_repository] = lambda: ProductRepository(test_db)
    app.dependency_overrides[get_payment_service] = lambda: mock_payment
    app.dependency_overrides[get_notification_service] = lambda: mock_notification
    app.dependency_overrides[get_idempotency_repository] = lambda: IdempotencyRepository(test_db)
    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)

    async with _ClientContext(test_db) as c:
        yield c


class TestCreateOrderIdempotency:
    async def test_returns_400_on_key_exceeding_128_characters(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        long_key = "x" * 129
        response = await order_client.post(
            "/orders/", json={"product_ids": product_ids},
            headers={**_auth_headers(Role.CUSTOMER), "Idempotency-Key": long_key},
        )
        assert response.status_code == 400


class TestCreateOrderStatus:
    async def test_returns_201_on_successful_payment(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        response = await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )
        assert response.status_code == 201

    async def test_returns_401_without_token(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        response = await order_client.post("/orders/", json={"product_ids": product_ids})
        assert response.status_code == 401

    async def test_returns_502_when_payment_fails(self, failing_payment_client: AsyncClient):
        product_ids = await _get_product_ids(failing_payment_client)
        response = await failing_payment_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )
        assert response.status_code == 502

    async def test_returns_422_on_missing_body(self, order_client: AsyncClient):
        response = await order_client.post("/orders/", json={}, headers=_auth_headers(Role.CUSTOMER))
        assert response.status_code == 422

    async def test_returns_422_for_unknown_product_ids(self, order_client: AsyncClient):
        response = await order_client.post(
            "/orders/", json={"product_ids": [str(uuid4())]}, headers=_auth_headers(Role.CUSTOMER)
        )
        assert response.status_code == 422


class TestCreateOrderResponse:
    async def test_response_contains_id(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        data = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert "id" in data

    async def test_order_status_is_waiting(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        data = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert data["status"] == "WAITING"

    async def test_total_price_is_computed_from_products(self, order_client: AsyncClient):
        menu = (await order_client.get("/menu")).json()
        variation = menu[0]["variations"][0]
        data = (await order_client.post(
            "/orders/", json={"product_ids": [variation["id"]]}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert data["total_price"] == variation["unit_price"]

    async def test_product_ids_match_request(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        data = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert set(data["product_ids"]) == set(product_ids)

    async def test_response_contains_user_id(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        data = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert "user_id" in data
        assert data["user_id"] == str(_DEFAULT_CUSTOMER_ID)


class TestCreateOrderPaymentError:
    async def test_error_detail_mentions_payment(self, failing_payment_client: AsyncClient):
        product_ids = await _get_product_ids(failing_payment_client)
        data = (await failing_payment_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        assert "payment" in data["detail"].lower()


class TestUpdateOrderStatusAccess:
    async def test_returns_403_for_customer_role(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers=_auth_headers(Role.CUSTOMER),
        )
        assert response.status_code == 403

    async def test_returns_401_without_token(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
        )
        assert response.status_code == 401

    async def test_returns_200_for_manager_role(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers=_auth_headers(Role.MANAGER),
        )
        assert response.status_code == 200


class TestUpdateOrderStatusTransitions:
    async def test_valid_transition_waiting_to_preparation(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        data = (await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers=_auth_headers(Role.MANAGER),
        )).json()
        assert data["status"] == OrderStatus.PREPARATION.value

    async def test_invalid_transition_waiting_to_ready(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.READY.value},
            headers=_auth_headers(Role.MANAGER),
        )
        assert response.status_code == 422

    async def test_invalid_transition_waiting_to_delivered(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.DELIVERED.value},
            headers=_auth_headers(Role.MANAGER),
        )
        assert response.status_code == 422

    async def test_full_transition_chain(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        for new_status in [OrderStatus.PREPARATION, OrderStatus.READY, OrderStatus.DELIVERED]:
            data = (await order_client.patch(
                f"/orders/{order_id}/status",
                json={"status": new_status.value},
                headers=_auth_headers(Role.MANAGER),
            )).json()
            assert data["status"] == new_status.value

    async def test_returns_404_for_unknown_order(self, order_client: AsyncClient):
        response = await order_client.patch(
            f"/orders/{uuid4()}/status",
            json={"status": OrderStatus.PREPARATION.value},
            headers=_auth_headers(Role.MANAGER),
        )
        assert response.status_code == 404

    async def test_transition_error_detail_message(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        data = (await order_client.patch(
            f"/orders/{order_id}/status",
            json={"status": OrderStatus.DELIVERED.value},
            headers=_auth_headers(Role.MANAGER),
        )).json()
        assert "Cannot transition" in data["detail"]


class TestGetOrderDetail:
    async def test_returns_404_for_unknown_order(self, order_client: AsyncClient):
        response = await order_client.get(f"/orders/{uuid4()}", headers=_auth_headers(Role.CUSTOMER))
        assert response.status_code == 404

    async def test_returns_401_without_token(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.get(f"/orders/{order_id}")
        assert response.status_code == 401

    async def test_returns_200_for_own_order(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.get(f"/orders/{order_id}", headers=_auth_headers(Role.CUSTOMER))
        assert response.status_code == 200

    async def test_returns_404_for_other_users_order(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        other_customer = _auth_headers(Role.CUSTOMER, user_id=uuid4())
        response = await order_client.get(f"/orders/{order_id}", headers=other_customer)
        assert response.status_code == 404

    async def test_manager_can_view_any_order(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        response = await order_client.get(f"/orders/{order_id}", headers=_auth_headers(Role.MANAGER))
        assert response.status_code == 200

    async def test_response_contains_required_fields(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        data = (await order_client.get(f"/orders/{order_id}", headers=_auth_headers(Role.CUSTOMER))).json()
        assert "id" in data
        assert "status" in data
        assert "total_price" in data
        assert "created_at" in data
        assert "items" in data

    async def test_detail_matches_created_order(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client, count=1)
        created = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()
        data = (await order_client.get(f"/orders/{created['id']}", headers=_auth_headers(Role.CUSTOMER))).json()
        assert data["id"] == created["id"]
        assert data["status"] == "WAITING"
        assert data["total_price"] == created["total_price"]

    async def test_items_contain_product_details(self, order_client: AsyncClient):
        product_ids = await _get_product_ids(order_client, count=1)
        order_id = (await order_client.post(
            "/orders/", json={"product_ids": product_ids}, headers=_auth_headers(Role.CUSTOMER)
        )).json()["id"]
        data = (await order_client.get(f"/orders/{order_id}", headers=_auth_headers(Role.CUSTOMER))).json()
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert "variation" in item
        assert "unit_price" in item

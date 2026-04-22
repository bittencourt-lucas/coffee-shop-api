from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.entities import Product
from src.core.enums import OrderStatus
from src.core.exceptions import InvalidProductError, PaymentFailedError
from src.use_cases.order import CreateOrder

_USER_ID = uuid4()


def _make_product(base_price: str = "3.00", price_change: str = "0.50") -> Product:
    return Product(
        id=uuid4(),
        name="Latte",
        base_price=Decimal(base_price),
        variation="Vanilla",
        price_change=Decimal(price_change),
    )


@pytest.fixture
def order_repo() -> AsyncMock:
    mock = AsyncMock()
    mock.create.side_effect = lambda order: order
    return mock


@pytest.fixture
def product_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def payment_service() -> AsyncMock:
    mock = AsyncMock()
    mock.process.return_value = {"id": "pay-123", "status": "approved"}
    return mock


@pytest.fixture
def failing_payment_service() -> AsyncMock:
    mock = AsyncMock()
    mock.process.side_effect = PaymentFailedError("declined")
    return mock


async def test_calls_payment_service_with_computed_total(order_repo, product_repo, payment_service):
    product = _make_product(base_price="3.00", price_change="0.50")
    product_repo.get_by_ids.return_value = [product]

    await CreateOrder(order_repo, product_repo, payment_service).execute([product.id], user_id=_USER_ID)

    payment_service.process.assert_called_once_with(Decimal("3.50"))


async def test_total_price_is_sum_of_all_products(order_repo, product_repo, payment_service):
    products = [_make_product("2.50", "0.00"), _make_product("4.00", "0.30")]
    product_repo.get_by_ids.return_value = products

    order = await CreateOrder(order_repo, product_repo, payment_service).execute(
        [p.id for p in products], user_id=_USER_ID
    )

    assert order.total_price == Decimal("6.80")


async def test_creates_order_in_repository_after_successful_payment(order_repo, product_repo, payment_service):
    product = _make_product()
    product_repo.get_by_ids.return_value = [product]

    await CreateOrder(order_repo, product_repo, payment_service).execute([product.id], user_id=_USER_ID)

    order_repo.create.assert_called_once()


async def test_created_order_has_waiting_status(order_repo, product_repo, payment_service):
    product = _make_product()
    product_repo.get_by_ids.return_value = [product]

    order = await CreateOrder(order_repo, product_repo, payment_service).execute([product.id], user_id=_USER_ID)

    assert order.status == OrderStatus.WAITING


async def test_raises_invalid_product_error_for_unknown_ids(order_repo, product_repo, payment_service):
    product_repo.get_by_ids.return_value = []

    with pytest.raises(InvalidProductError):
        await CreateOrder(order_repo, product_repo, payment_service).execute([uuid4()], user_id=_USER_ID)


async def test_does_not_charge_payment_when_products_are_invalid(order_repo, product_repo, payment_service):
    product_repo.get_by_ids.return_value = []

    with pytest.raises(InvalidProductError):
        await CreateOrder(order_repo, product_repo, payment_service).execute([uuid4()], user_id=_USER_ID)

    payment_service.process.assert_not_called()


async def test_does_not_create_order_when_products_are_invalid(order_repo, product_repo, payment_service):
    product_repo.get_by_ids.return_value = []

    with pytest.raises(InvalidProductError):
        await CreateOrder(order_repo, product_repo, payment_service).execute([uuid4()], user_id=_USER_ID)

    order_repo.create.assert_not_called()


async def test_propagates_payment_failed_error(order_repo, product_repo, failing_payment_service):
    product = _make_product()
    product_repo.get_by_ids.return_value = [product]

    with pytest.raises(PaymentFailedError):
        await CreateOrder(order_repo, product_repo, failing_payment_service).execute([product.id], user_id=_USER_ID)


async def test_does_not_create_order_when_payment_fails(order_repo, product_repo, failing_payment_service):
    product = _make_product()
    product_repo.get_by_ids.return_value = [product]

    with pytest.raises(PaymentFailedError):
        await CreateOrder(order_repo, product_repo, failing_payment_service).execute([product.id], user_id=_USER_ID)

    order_repo.create.assert_not_called()

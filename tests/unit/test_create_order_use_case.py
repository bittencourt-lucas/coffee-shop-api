import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.exceptions import PaymentFailedError
from src.use_cases.order import CreateOrder


@pytest.fixture
def repo() -> AsyncMock:
    mock = AsyncMock()
    mock.create.return_value = Order(
        id=uuid4(),
        status=OrderStatus.WAITING,
        total_price=15.50,
        product_ids=[],
    )
    return mock


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


async def test_calls_payment_service_with_total_price(repo, payment_service):
    await CreateOrder(repo, payment_service).execute([uuid4()], total_price=15.50)
    payment_service.process.assert_called_once_with(15.50)


async def test_creates_order_in_repository_after_successful_payment(repo, payment_service):
    await CreateOrder(repo, payment_service).execute([uuid4()], total_price=15.50)
    repo.create.assert_called_once()


async def test_created_order_has_waiting_status(repo, payment_service):
    order = await CreateOrder(repo, payment_service).execute([uuid4()], total_price=15.50)
    assert order.status == OrderStatus.WAITING


async def test_propagates_payment_failed_error(repo, failing_payment_service):
    with pytest.raises(PaymentFailedError):
        await CreateOrder(repo, failing_payment_service).execute([uuid4()], total_price=10.0)


async def test_does_not_create_order_when_payment_fails(repo, failing_payment_service):
    with pytest.raises(PaymentFailedError):
        await CreateOrder(repo, failing_payment_service).execute([uuid4()], total_price=10.0)
    repo.create.assert_not_called()

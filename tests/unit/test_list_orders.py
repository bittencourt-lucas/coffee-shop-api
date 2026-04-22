from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.entities import Order
from src.core.enums import OrderStatus, Role
from src.use_cases.order import ListOrders

_USER_ID = uuid4()
_OTHER_USER_ID = uuid4()


def _make_order(user_id=None) -> Order:
    return Order(
        id=uuid4(),
        status=OrderStatus.WAITING,
        total_price=Decimal("5.00"),
        user_id=user_id or _USER_ID,
        product_ids=[],
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


async def test_manager_calls_list_all(repo):
    repo.list_all.return_value = ([], 0)

    await ListOrders(repo).execute(user_id=_USER_ID, role=Role.MANAGER)

    repo.list_all.assert_called_once()
    repo.list_for_user.assert_not_called()


async def test_customer_calls_list_for_user(repo):
    repo.list_for_user.return_value = ([], 0)

    await ListOrders(repo).execute(user_id=_USER_ID, role=Role.CUSTOMER)

    repo.list_for_user.assert_called_once()
    repo.list_all.assert_not_called()


async def test_customer_passes_user_id_to_repo(repo):
    repo.list_for_user.return_value = ([], 0)

    await ListOrders(repo).execute(user_id=_USER_ID, role=Role.CUSTOMER)

    repo.list_for_user.assert_called_once_with(user_id=_USER_ID, offset=0, limit=20)


async def test_manager_passes_pagination_params(repo):
    repo.list_all.return_value = ([], 0)

    await ListOrders(repo).execute(user_id=_USER_ID, role=Role.MANAGER, offset=40, limit=10)

    repo.list_all.assert_called_once_with(offset=40, limit=10)


async def test_customer_passes_pagination_params(repo):
    repo.list_for_user.return_value = ([], 0)

    await ListOrders(repo).execute(user_id=_USER_ID, role=Role.CUSTOMER, offset=20, limit=5)

    repo.list_for_user.assert_called_once_with(user_id=_USER_ID, offset=20, limit=5)


async def test_returns_orders_and_total(repo):
    orders = [_make_order(), _make_order()]
    repo.list_all.return_value = (orders, 2)

    result_orders, total = await ListOrders(repo).execute(user_id=_USER_ID, role=Role.MANAGER)

    assert result_orders == orders
    assert total == 2


async def test_returns_empty_list_when_no_orders(repo):
    repo.list_for_user.return_value = ([], 0)

    orders, total = await ListOrders(repo).execute(user_id=_USER_ID, role=Role.CUSTOMER)

    assert orders == []
    assert total == 0

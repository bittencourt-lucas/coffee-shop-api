from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.entities import Product
from src.use_cases.product import GetMenu


def _make_product(
    name: str, base_price: str, variation: str, price_change: str
) -> Product:
    return Product(
        id=uuid4(),
        name=name,
        base_price=Decimal(base_price),
        variation=variation,
        price_change=Decimal(price_change),
    )


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


async def test_returns_empty_list_when_no_products(repo):
    repo.list_all.return_value = ([], 0)

    items, total = await GetMenu(repo).execute()

    assert items == []
    assert total == 0


async def test_calls_list_all_once(repo):
    repo.list_all.return_value = ([], 0)

    await GetMenu(repo).execute()

    repo.list_all.assert_called_once()


async def test_groups_same_name_products_into_one_menu_item(repo):
    repo.list_all.return_value = (
        [
            _make_product("Latte", "4.00", "Vanilla", "0.30"),
            _make_product("Latte", "4.00", "Hazelnut", "0.40"),
            _make_product("Latte", "4.00", "Pumpkin Spice", "0.50"),
        ],
        1,
    )

    items, _ = await GetMenu(repo).execute()

    assert len(items) == 1
    assert items[0].name == "Latte"


async def test_produces_one_menu_item_per_distinct_product_name(repo):
    repo.list_all.return_value = (
        [
            _make_product("Latte", "4.00", "Vanilla", "0.30"),
            _make_product("Espresso", "2.50", "Single Shot", "0.00"),
            _make_product("Espresso", "2.50", "Double Shot", "1.00"),
        ],
        2,
    )

    items, _ = await GetMenu(repo).execute()

    assert len(items) == 2
    names = {item.name for item in items}
    assert names == {"Latte", "Espresso"}


async def test_menu_item_contains_all_variations(repo):
    repo.list_all.return_value = (
        [
            _make_product("Latte", "4.00", "Vanilla", "0.30"),
            _make_product("Latte", "4.00", "Hazelnut", "0.40"),
            _make_product("Latte", "4.00", "Pumpkin Spice", "0.50"),
        ],
        1,
    )

    items, _ = await GetMenu(repo).execute()

    latte = items[0]
    variation_names = {v.variation for v in latte.variations}
    assert variation_names == {"Vanilla", "Hazelnut", "Pumpkin Spice"}


async def test_variation_unit_prices_are_computed_correctly(repo):
    repo.list_all.return_value = (
        [
            _make_product("Espresso", "2.50", "Single Shot", "0.00"),
            _make_product("Espresso", "2.50", "Double Shot", "1.00"),
        ],
        1,
    )

    items, _ = await GetMenu(repo).execute()

    espresso = items[0]
    unit_prices = {v.variation: v.unit_price for v in espresso.variations}
    assert unit_prices["Single Shot"] == Decimal("2.50")
    assert unit_prices["Double Shot"] == Decimal("3.50")


async def test_each_variation_exposes_its_product_id(repo):
    product = _make_product("Espresso", "2.50", "Single Shot", "0.00")
    repo.list_all.return_value = ([product], 1)

    items, _ = await GetMenu(repo).execute()

    assert items[0].variations[0].id == product.id


async def test_menu_item_base_price_is_preserved(repo):
    repo.list_all.return_value = (
        [
            _make_product("Iced Coffee", "3.50", "Regular", "0.00"),
            _make_product("Iced Coffee", "3.50", "Sweetened", "0.30"),
        ],
        1,
    )

    items, _ = await GetMenu(repo).execute()

    assert items[0].base_price == Decimal("3.50")


async def test_single_variation_product_has_one_variation(repo):
    repo.list_all.return_value = (
        [_make_product("Espresso", "2.50", "Single Shot", "0.00")],
        1,
    )

    items, _ = await GetMenu(repo).execute()

    assert len(items[0].variations) == 1
    assert items[0].variations[0].variation == "Single Shot"


async def test_passes_offset_and_limit_to_repository(repo):
    repo.list_all.return_value = ([], 0)

    await GetMenu(repo).execute(offset=20, limit=10)

    repo.list_all.assert_called_once_with(offset=20, limit=10)


async def test_returns_total_from_repository(repo):
    repo.list_all.return_value = ([], 42)

    _, total = await GetMenu(repo).execute()

    assert total == 42

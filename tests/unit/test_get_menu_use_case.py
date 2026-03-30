from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.entities import Product
from src.use_cases.product import GetMenu


def _make_product(name: str, base_price: float, variation: str, price_change: float) -> Product:
    return Product(id=uuid4(), name=name, base_price=base_price, variation=variation, price_change=price_change)


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


async def test_returns_empty_list_when_no_products(repo):
    repo.list_all.return_value = []

    result = await GetMenu(repo).execute()

    assert result == []


async def test_calls_list_all_once(repo):
    repo.list_all.return_value = []

    await GetMenu(repo).execute()

    repo.list_all.assert_called_once()


async def test_groups_same_name_products_into_one_menu_item(repo):
    repo.list_all.return_value = [
        _make_product("Latte", 4.0, "Vanilla", 0.30),
        _make_product("Latte", 4.0, "Hazelnut", 0.40),
        _make_product("Latte", 4.0, "Pumpkin Spice", 0.50),
    ]

    result = await GetMenu(repo).execute()

    assert len(result) == 1
    assert result[0].name == "Latte"


async def test_produces_one_menu_item_per_distinct_product_name(repo):
    repo.list_all.return_value = [
        _make_product("Latte", 4.0, "Vanilla", 0.30),
        _make_product("Espresso", 2.5, "Single Shot", 0.00),
        _make_product("Espresso", 2.5, "Double Shot", 1.00),
    ]

    result = await GetMenu(repo).execute()

    assert len(result) == 2
    names = {item.name for item in result}
    assert names == {"Latte", "Espresso"}


async def test_menu_item_contains_all_variations(repo):
    repo.list_all.return_value = [
        _make_product("Latte", 4.0, "Vanilla", 0.30),
        _make_product("Latte", 4.0, "Hazelnut", 0.40),
        _make_product("Latte", 4.0, "Pumpkin Spice", 0.50),
    ]

    result = await GetMenu(repo).execute()

    latte = result[0]
    variation_names = {v.variation for v in latte.variations}
    assert variation_names == {"Vanilla", "Hazelnut", "Pumpkin Spice"}


async def test_variation_unit_prices_are_computed_correctly(repo):
    repo.list_all.return_value = [
        _make_product("Espresso", 2.5, "Single Shot", 0.00),
        _make_product("Espresso", 2.5, "Double Shot", 1.00),
    ]

    result = await GetMenu(repo).execute()

    espresso = result[0]
    unit_prices = {v.variation: v.unit_price for v in espresso.variations}
    assert unit_prices["Single Shot"] == 2.50
    assert unit_prices["Double Shot"] == 3.50


async def test_each_variation_exposes_its_product_id(repo):
    product = _make_product("Espresso", 2.5, "Single Shot", 0.00)
    repo.list_all.return_value = [product]

    result = await GetMenu(repo).execute()

    assert result[0].variations[0].id == product.id


async def test_menu_item_base_price_is_preserved(repo):
    repo.list_all.return_value = [
        _make_product("Iced Coffee", 3.5, "Regular", 0.00),
        _make_product("Iced Coffee", 3.5, "Sweetened", 0.30),
    ]

    result = await GetMenu(repo).execute()

    assert result[0].base_price == 3.5


async def test_single_variation_product_has_one_variation(repo):
    repo.list_all.return_value = [
        _make_product("Espresso", 2.5, "Single Shot", 0.00),
    ]

    result = await GetMenu(repo).execute()

    assert len(result[0].variations) == 1
    assert result[0].variations[0].variation == "Single Shot"

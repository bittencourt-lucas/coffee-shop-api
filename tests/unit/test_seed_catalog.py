from unittest.mock import AsyncMock, call

import pytest

from src.infrastructure.database.seed import CATALOG, seed_catalog


@pytest.fixture
def db() -> AsyncMock:
    return AsyncMock()


async def test_does_not_insert_when_table_already_has_products(db):
    db.fetch_val.return_value = 5

    await seed_catalog(db)

    db.execute_many.assert_not_called()


async def test_inserts_when_table_is_empty(db):
    db.fetch_val.return_value = 0

    await seed_catalog(db)

    db.execute_many.assert_called_once()


async def test_inserts_all_catalog_items(db):
    db.fetch_val.return_value = 0

    await seed_catalog(db)

    _, rows = db.execute_many.call_args.args
    assert len(rows) == len(CATALOG)


async def test_inserted_rows_have_all_required_fields(db):
    db.fetch_val.return_value = 0

    await seed_catalog(db)

    _, rows = db.execute_many.call_args.args
    for row in rows:
        assert "id" in row
        assert "name" in row
        assert "base_price" in row
        assert "variation" in row
        assert "price_change" in row


async def test_inserted_rows_have_unique_ids(db):
    db.fetch_val.return_value = 0

    await seed_catalog(db)

    _, rows = db.execute_many.call_args.args
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))


async def test_catalog_data_matches_expected_products(db):
    db.fetch_val.return_value = 0

    await seed_catalog(db)

    _, rows = db.execute_many.call_args.args
    names = {row["name"] for row in rows}
    assert names == {"Latte", "Espresso", "Macchiato", "Iced Coffee", "Donuts"}


async def test_seed_is_idempotent_on_second_call(db):
    """Second call with non-zero count must not insert again."""
    db.fetch_val.return_value = len(CATALOG)

    await seed_catalog(db)
    await seed_catalog(db)

    db.execute_many.assert_not_called()

from uuid import uuid4

import databases
import sqlalchemy

from src.infrastructure.database.models import products_table

_count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(products_table)

CATALOG = [
    {"name": "Latte",       "base_price": 4.00, "variation": "Pumpkin Spice", "price_change": 0.50},
    {"name": "Latte",       "base_price": 4.00, "variation": "Vanilla",       "price_change": 0.30},
    {"name": "Latte",       "base_price": 4.00, "variation": "Hazelnut",      "price_change": 0.40},
    {"name": "Espresso",    "base_price": 2.50, "variation": "Single Shot",   "price_change": 0.00},
    {"name": "Espresso",    "base_price": 2.50, "variation": "Double Shot",   "price_change": 1.00},
    {"name": "Macchiato",   "base_price": 4.00, "variation": "Caramel",       "price_change": 0.50},
    {"name": "Macchiato",   "base_price": 4.00, "variation": "Vanilla",       "price_change": 0.30},
    {"name": "Iced Coffee", "base_price": 3.50, "variation": "Regular",       "price_change": 0.00},
    {"name": "Iced Coffee", "base_price": 3.50, "variation": "Sweetened",     "price_change": 0.30},
    {"name": "Iced Coffee", "base_price": 3.50, "variation": "Extra Ice",     "price_change": 0.20},
    {"name": "Donuts",      "base_price": 2.00, "variation": "Glazed",        "price_change": 0.00},
    {"name": "Donuts",      "base_price": 2.00, "variation": "Jelly",         "price_change": 0.30},
    {"name": "Donuts",      "base_price": 2.00, "variation": "Boston Cream",  "price_change": 0.50},
]


async def seed_catalog(db: databases.Database) -> None:
    count = await db.fetch_val(_count_query)
    if count:
        return

    await db.execute_many(
        products_table.insert(),
        [{"id": str(uuid4()), **item} for item in CATALOG],
    )

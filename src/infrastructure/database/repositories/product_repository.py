from decimal import Decimal
from uuid import UUID

import databases
import sqlalchemy

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository
from src.infrastructure.database.models import products_table


class ProductRepository(AbstractProductRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def list_all(self, offset: int = 0, limit: int = 20) -> tuple[list[Product], int]:
        count_query = sqlalchemy.select(
            sqlalchemy.func.count(sqlalchemy.distinct(products_table.c.name))
        )
        total = await self._db.fetch_val(count_query)

        names_query = (
            sqlalchemy.select(sqlalchemy.distinct(products_table.c.name))
            .order_by(products_table.c.name)
            .limit(limit)
            .offset(offset)
        )
        name_rows = await self._db.fetch_all(names_query)
        names = [row[0] for row in name_rows]

        if not names:
            return [], total

        products_query = products_table.select().where(products_table.c.name.in_(names))
        rows = await self._db.fetch_all(products_query)
        return [self._to_entity(row) for row in rows], total

    async def get_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        query = products_table.select().where(
            products_table.c.id.in_([str(pid) for pid in product_ids])
        )
        rows = await self._db.fetch_all(query)
        return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_entity(row) -> Product:
        return Product(
            id=UUID(row["id"]),
            name=row["name"],
            base_price=Decimal(str(row["base_price"])).quantize(Decimal("0.01")),
            variation=row["variation"],
            price_change=Decimal(str(row["price_change"])).quantize(Decimal("0.01")),
        )

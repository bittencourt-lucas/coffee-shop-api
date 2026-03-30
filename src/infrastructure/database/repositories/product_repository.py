from uuid import UUID

import databases

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository
from src.infrastructure.database.models import products_table


class ProductRepository(AbstractProductRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def list_all(self) -> list[Product]:
        rows = await self._db.fetch_all(products_table.select())
        return [self._to_entity(row) for row in rows]

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
            base_price=row["base_price"],
            variation=row["variation"],
            price_change=row["price_change"],
        )

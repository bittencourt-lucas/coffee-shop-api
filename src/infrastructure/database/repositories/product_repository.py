from uuid import UUID

import databases

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository
from src.infrastructure.database.models import products_table


class ProductRepository(AbstractProductRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def create(self, product: Product) -> Product:
        query = products_table.insert().values(
            id=str(product.id),
            name=product.name,
            base_price=product.base_price,
            variation=product.variation,
            price_change=product.price_change,
        )
        await self._db.execute(query)
        return product

    async def get_by_id(self, product_id: UUID) -> Product | None:
        query = products_table.select().where(products_table.c.id == str(product_id))
        row = await self._db.fetch_one(query)
        return self._to_entity(row) if row else None

    async def list_all(self) -> list[Product]:
        query = products_table.select()
        rows = await self._db.fetch_all(query)
        return [self._to_entity(row) for row in rows]

    async def update(self, product: Product) -> Product:
        query = (
            products_table.update()
            .where(products_table.c.id == str(product.id))
            .values(
                name=product.name,
                base_price=product.base_price,
                variation=product.variation,
                price_change=product.price_change,
            )
        )
        await self._db.execute(query)
        return product

    async def delete(self, product_id: UUID) -> None:
        query = products_table.delete().where(products_table.c.id == str(product_id))
        await self._db.execute(query)

    @staticmethod
    def _to_entity(row) -> Product:
        return Product(
            id=UUID(row["id"]),
            name=row["name"],
            base_price=row["base_price"],
            variation=row["variation"],
            price_change=row["price_change"],
        )

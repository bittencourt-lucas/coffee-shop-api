from uuid import UUID

import databases
import sqlalchemy

from src.core.entities import Order, OrderDetail, OrderItem
from src.core.enums import OrderStatus
from src.core.repositories import AbstractOrderRepository
from src.infrastructure.database.models import orders_table, order_products_table, products_table


class OrderRepository(AbstractOrderRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def create(self, order: Order) -> Order:
        async with self._db.transaction():
            await self._db.execute(
                orders_table.insert().values(
                    id=str(order.id),
                    status=order.status.value,
                    total_price=order.total_price,
                )
            )
            if order.product_ids:
                await self._db.execute_many(
                    order_products_table.insert(),
                    [
                        {"order_id": str(order.id), "product_id": str(pid)}
                        for pid in order.product_ids
                    ],
                )
        return order

    async def get_by_id(self, order_id: UUID) -> Order | None:
        row = await self._db.fetch_one(
            orders_table.select().where(orders_table.c.id == str(order_id))
        )
        if not row:
            return None
        product_ids = await self._fetch_product_ids(order_id)
        return self._to_entity(row, product_ids)

    async def get_detail_by_id(self, order_id: UUID) -> OrderDetail | None:
        row = await self._db.fetch_one(
            orders_table.select().where(orders_table.c.id == str(order_id))
        )
        if not row:
            return None
        items = await self._fetch_order_items(order_id)
        return OrderDetail(
            id=UUID(row["id"]),
            status=OrderStatus(row["status"]),
            total_price=row["total_price"],
            created_at=row["created_at"],
            items=items,
        )

    async def list_all(self) -> list[Order]:
        rows = await self._db.fetch_all(orders_table.select())
        orders = []
        for row in rows:
            product_ids = await self._fetch_product_ids(UUID(row["id"]))
            orders.append(self._to_entity(row, product_ids))
        return orders

    async def update_status(self, order_id: UUID, status: OrderStatus) -> Order:
        await self._db.execute(
            orders_table.update()
            .where(orders_table.c.id == str(order_id))
            .values(status=status.value)
        )
        return await self.get_by_id(order_id)

    async def _fetch_product_ids(self, order_id: UUID) -> list[UUID]:
        rows = await self._db.fetch_all(
            order_products_table.select().where(
                order_products_table.c.order_id == str(order_id)
            )
        )
        return [UUID(row["product_id"]) for row in rows]

    async def _fetch_order_items(self, order_id: UUID) -> list[OrderItem]:
        query = (
            sqlalchemy.select(
                products_table.c.id,
                products_table.c.name,
                products_table.c.variation,
                (products_table.c.base_price + products_table.c.price_change).label("unit_price"),
            )
            .select_from(
                order_products_table.join(
                    products_table,
                    order_products_table.c.product_id == products_table.c.id,
                )
            )
            .where(order_products_table.c.order_id == str(order_id))
        )
        rows = await self._db.fetch_all(query)
        return [
            OrderItem(
                id=UUID(row["id"]),
                name=row["name"],
                variation=row["variation"],
                unit_price=row["unit_price"],
            )
            for row in rows
        ]

    @staticmethod
    def _to_entity(row, product_ids: list[UUID]) -> Order:
        return Order(
            id=UUID(row["id"]),
            status=OrderStatus(row["status"]),
            total_price=row["total_price"],
            product_ids=product_ids,
        )

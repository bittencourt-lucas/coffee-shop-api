from uuid import UUID

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.repositories import AbstractOrderRepository


class UpdateOrderStatus:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: UUID, status: OrderStatus) -> Order | None:
        existing = await self._repository.get_by_id(order_id)
        if not existing:
            return None
        return await self._repository.update_status(order_id, status)

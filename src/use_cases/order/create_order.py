from uuid import UUID, uuid4

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.repositories import AbstractOrderRepository


class CreateOrder:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UUID, product_ids: list[UUID], total_price: float) -> Order:
        order = Order(
            id=uuid4(),
            status=OrderStatus.WAITING,
            total_price=total_price,
            user_id=user_id,
            product_ids=product_ids,
        )
        return await self._repository.create(order)

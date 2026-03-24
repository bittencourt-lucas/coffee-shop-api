from uuid import UUID

from src.core.entities import Order
from src.core.repositories import AbstractOrderRepository


class GetOrder:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: UUID) -> Order | None:
        return await self._repository.get_by_id(order_id)

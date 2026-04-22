from uuid import UUID

from src.core.entities import OrderDetail
from src.core.repositories import AbstractOrderRepository


class GetOrderDetail:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: UUID, user_id: UUID | None = None) -> OrderDetail | None:
        if user_id is not None:
            return await self._repository.get_detail_by_id_for_user(order_id, user_id)
        return await self._repository.get_detail_by_id(order_id)

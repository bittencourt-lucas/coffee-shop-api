from src.core.entities import Order
from src.core.repositories import AbstractOrderRepository


class ListOrders:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Order]:
        return await self._repository.list_all()

from uuid import UUID

from src.core.entities import Order
from src.core.enums import Role
from src.core.repositories import AbstractOrderRepository


class ListOrders:
    def __init__(self, repository: AbstractOrderRepository) -> None:
        self._repository = repository

    async def execute(
        self, user_id: UUID, role: Role, offset: int = 0, limit: int = 20
    ) -> tuple[list[Order], int]:
        if role == Role.MANAGER:
            return await self._repository.list_all(offset=offset, limit=limit)
        return await self._repository.list_for_user(user_id=user_id, offset=offset, limit=limit)

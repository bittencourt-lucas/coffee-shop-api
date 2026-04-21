from uuid import UUID

from src.core.entities import User
from src.core.repositories import AbstractUserRepository


class GetUser:
    def __init__(self, repository: AbstractUserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UUID) -> User | None:
        return await self._repository.get_by_id(user_id)

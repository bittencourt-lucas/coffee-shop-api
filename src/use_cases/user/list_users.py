from src.core.entities import User
from src.core.repositories import AbstractUserRepository


class ListUsers:
    def __init__(self, repository: AbstractUserRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[User]:
        return await self._repository.list_all()

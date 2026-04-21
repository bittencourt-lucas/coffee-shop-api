from uuid import uuid4

from src.core.entities import User
from src.core.enums import Role
from src.core.repositories import AbstractUserRepository


class CreateUser:
    def __init__(self, repository: AbstractUserRepository) -> None:
        self._repository = repository

    async def execute(self, email: str, role: Role) -> User:
        user = User(id=uuid4(), email=email, role=role)
        return await self._repository.create(user)

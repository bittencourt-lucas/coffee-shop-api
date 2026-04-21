from uuid import uuid4

from src.core.entities import User
from src.core.enums import Role
from src.core.repositories import AbstractUserRepository
from src.infrastructure.auth.password import hash_password


class CreateUser:
    def __init__(self, repository: AbstractUserRepository) -> None:
        self._repository = repository

    async def execute(self, email: str, role: Role, password: str) -> User:
        user = User(id=uuid4(), email=email, role=role, password_hash=hash_password(password))
        return await self._repository.create(user)

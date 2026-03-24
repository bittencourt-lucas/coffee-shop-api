from abc import ABC, abstractmethod
from uuid import UUID

from src.core.entities import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[User]:
        raise NotImplementedError

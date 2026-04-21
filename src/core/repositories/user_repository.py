import uuid
from abc import ABC, abstractmethod

from src.core.entities.user import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        pass

    @abstractmethod
    async def list_all(self) -> list[User]:
        pass

from abc import ABC, abstractmethod
from uuid import UUID

from src.core.entities import Product


class AbstractProductRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        raise NotImplementedError

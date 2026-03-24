from abc import ABC, abstractmethod
from uuid import UUID

from src.core.entities import Product


class AbstractProductRepository(ABC):
    @abstractmethod
    async def create(self, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, product: Product) -> Product:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, product_id: UUID) -> None:
        raise NotImplementedError

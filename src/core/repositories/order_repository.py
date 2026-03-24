from abc import ABC, abstractmethod
from uuid import UUID

from src.core.entities import Order
from src.core.enums import OrderStatus


class AbstractOrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, order_id: UUID, status: OrderStatus) -> Order:
        raise NotImplementedError

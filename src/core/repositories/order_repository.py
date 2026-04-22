from abc import ABC, abstractmethod
from uuid import UUID

from src.core.entities import Order, OrderDetail
from src.core.enums import OrderStatus


class AbstractOrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def get_detail_by_id(self, order_id: UUID) -> OrderDetail | None:
        raise NotImplementedError

    @abstractmethod
    async def get_detail_by_id_for_user(self, order_id: UUID, user_id: UUID) -> OrderDetail | None:
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, order_id: UUID, status: OrderStatus) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, offset: int = 0, limit: int = 20) -> tuple[list[Order], int]:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, user_id: UUID, offset: int = 0, limit: int = 20) -> tuple[list[Order], int]:
        raise NotImplementedError

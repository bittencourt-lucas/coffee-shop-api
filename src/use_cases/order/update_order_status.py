from uuid import UUID

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.exceptions import InvalidStatusTransitionError
from src.core.repositories import AbstractOrderRepository
from src.core.services import AbstractNotificationService

_TRANSITIONS: dict[OrderStatus, OrderStatus] = {
    OrderStatus.WAITING: OrderStatus.PREPARATION,
    OrderStatus.PREPARATION: OrderStatus.READY,
    OrderStatus.READY: OrderStatus.DELIVERED,
}


class UpdateOrderStatus:
    def __init__(
        self,
        repository: AbstractOrderRepository,
        notification_service: AbstractNotificationService,
    ) -> None:
        self._repository = repository
        self._notification_service = notification_service

    async def execute(self, order_id: UUID, new_status: OrderStatus) -> Order | None:
        existing = await self._repository.get_by_id(order_id)
        if not existing:
            return None
        if _TRANSITIONS.get(existing.status) != new_status:
            raise InvalidStatusTransitionError(existing.status.value, new_status.value)
        order = await self._repository.update_status(order_id, new_status)
        await self._notification_service.notify(new_status.value)
        return order

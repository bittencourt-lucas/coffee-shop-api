from uuid import UUID, uuid4

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.repositories import AbstractOrderRepository
from src.core.services import AbstractPaymentService


class CreateOrder:
    def __init__(self, repository: AbstractOrderRepository, payment_service: AbstractPaymentService) -> None:
        self._repository = repository
        self._payment_service = payment_service

    async def execute(self, product_ids: list[UUID], total_price: float) -> Order:
        await self._payment_service.process(total_price)

        order = Order(
            id=uuid4(),
            status=OrderStatus.WAITING,
            total_price=total_price,
            product_ids=product_ids,
        )
        return await self._repository.create(order)

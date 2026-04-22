from decimal import Decimal
from uuid import UUID, uuid4

from src.core.entities import Order
from src.core.enums import OrderStatus
from src.core.exceptions import InvalidProductError
from src.core.repositories import AbstractOrderRepository, AbstractProductRepository
from src.core.services import AbstractPaymentService


class CreateOrder:
    def __init__(
        self,
        order_repository: AbstractOrderRepository,
        product_repository: AbstractProductRepository,
        payment_service: AbstractPaymentService,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._payment_service = payment_service

    async def execute(self, product_ids: list[UUID], user_id: UUID) -> Order:
        products = await self._product_repository.get_by_ids(product_ids)

        if len(products) != len(product_ids):
            found_ids = {p.id for p in products}
            missing_ids = [pid for pid in product_ids if pid not in found_ids]
            raise InvalidProductError(missing_ids)

        total_price = sum(
            (p.base_price + p.price_change for p in products), Decimal(0)
        ).quantize(Decimal("0.01"))

        await self._payment_service.process(total_price)

        order = Order(
            id=uuid4(),
            status=OrderStatus.WAITING,
            total_price=total_price,
            user_id=user_id,
            product_ids=product_ids,
        )
        return await self._order_repository.create(order)

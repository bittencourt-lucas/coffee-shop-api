from uuid import UUID

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository


class UpdateProduct:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        product_id: UUID,
        name: str,
        base_price: float,
        variation: str,
        price_change: float,
    ) -> Product | None:
        existing = await self._repository.get_by_id(product_id)
        if not existing:
            return None
        updated = Product(
            id=product_id,
            name=name,
            base_price=base_price,
            variation=variation,
            price_change=price_change,
        )
        return await self._repository.update(updated)

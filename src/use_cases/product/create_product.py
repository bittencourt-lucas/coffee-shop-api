from uuid import uuid4

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository


class CreateProduct:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self, name: str, base_price: float, variation: str, price_change: float) -> Product:
        product = Product(
            id=uuid4(),
            name=name,
            base_price=base_price,
            variation=variation,
            price_change=price_change,
        )
        return await self._repository.create(product)

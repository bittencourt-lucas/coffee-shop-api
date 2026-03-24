from uuid import UUID

from src.core.entities import Product
from src.core.repositories import AbstractProductRepository


class GetProduct:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self, product_id: UUID) -> Product | None:
        return await self._repository.get_by_id(product_id)

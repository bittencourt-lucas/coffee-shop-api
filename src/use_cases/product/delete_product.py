from uuid import UUID

from src.core.repositories import AbstractProductRepository


class DeleteProduct:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self, product_id: UUID) -> bool:
        existing = await self._repository.get_by_id(product_id)
        if not existing:
            return False
        await self._repository.delete(product_id)
        return True

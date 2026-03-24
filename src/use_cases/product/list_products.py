from src.core.entities import Product
from src.core.repositories import AbstractProductRepository


class ListProducts:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Product]:
        return await self._repository.list_all()

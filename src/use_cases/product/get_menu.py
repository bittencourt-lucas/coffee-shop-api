from collections import defaultdict

from src.core.entities import MenuItem, MenuVariation
from src.core.repositories import AbstractProductRepository


class GetMenu:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[MenuItem]:
        products = await self._repository.list_all()

        grouped: dict[tuple, list[MenuVariation]] = defaultdict(list)
        for product in products:
            key = (product.name, product.base_price)
            grouped[key].append(
                MenuVariation(
                    id=product.id,
                    variation=product.variation,
                    unit_price=round(product.base_price + product.price_change, 2),
                )
            )

        return [
            MenuItem(name=name, base_price=base_price, variations=variations)
            for (name, base_price), variations in grouped.items()
        ]

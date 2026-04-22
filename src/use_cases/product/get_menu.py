from collections import defaultdict
from decimal import Decimal

from src.core.entities import MenuItem, MenuVariation
from src.core.repositories import AbstractProductRepository


class GetMenu:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self, offset: int = 0, limit: int = 20) -> tuple[list[MenuItem], int]:
        products, total = await self._repository.list_all(offset=offset, limit=limit)

        grouped: dict[tuple, list[MenuVariation]] = defaultdict(list)
        for product in products:
            key = (product.name, product.base_price)
            grouped[key].append(
                MenuVariation(
                    id=product.id,
                    variation=product.variation,
                    unit_price=(product.base_price + product.price_change).quantize(Decimal("0.01")),
                )
            )

        items = [
            MenuItem(name=name, base_price=base_price, variations=variations)
            for (name, base_price), variations in grouped.items()
        ]
        return items, total

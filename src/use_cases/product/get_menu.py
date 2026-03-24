from collections import defaultdict

from src.core.repositories import AbstractProductRepository


class MenuVariation:
    def __init__(self, variation: str, price_change: float) -> None:
        self.variation = variation
        self.price_change = price_change


class MenuItem:
    def __init__(self, name: str, base_price: float, variations: list[MenuVariation]) -> None:
        self.name = name
        self.base_price = base_price
        self.variations = variations


class GetMenu:
    def __init__(self, repository: AbstractProductRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[MenuItem]:
        products = await self._repository.list_all()

        grouped: dict[tuple, list[MenuVariation]] = defaultdict(list)
        for product in products:
            key = (product.name, product.base_price)
            grouped[key].append(MenuVariation(product.variation, product.price_change))

        return [
            MenuItem(name=name, base_price=base_price, variations=variations)
            for (name, base_price), variations in grouped.items()
        ]

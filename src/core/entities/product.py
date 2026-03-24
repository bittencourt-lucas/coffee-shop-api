from dataclasses import dataclass
from uuid import UUID


@dataclass
class Product:
    id: UUID
    name: str
    base_price: float
    variation: str
    price_change: float

from dataclasses import dataclass
from uuid import UUID


@dataclass
class OrderItem:
    id: UUID
    name: str
    variation: str
    unit_price: float  # base_price + price_change

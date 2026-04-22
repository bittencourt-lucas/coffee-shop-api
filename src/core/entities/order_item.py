from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class OrderItem:
    id: UUID
    name: str
    variation: str
    unit_price: Decimal

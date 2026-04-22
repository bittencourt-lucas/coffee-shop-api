from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class Product:
    id: UUID
    name: str
    base_price: Decimal
    variation: str
    price_change: Decimal

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass
class MenuVariation:
    id: UUID
    variation: str
    unit_price: Decimal


@dataclass
class MenuItem:
    name: str
    base_price: Decimal
    variations: list[MenuVariation] = field(default_factory=list)

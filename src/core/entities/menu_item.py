from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class MenuVariation:
    id: UUID
    variation: str
    unit_price: float


@dataclass
class MenuItem:
    name: str
    base_price: float
    variations: list[MenuVariation] = field(default_factory=list)

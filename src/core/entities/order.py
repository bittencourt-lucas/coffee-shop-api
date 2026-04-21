from dataclasses import dataclass, field
from uuid import UUID

from src.core.enums import OrderStatus


@dataclass
class Order:
    id: UUID
    status: OrderStatus
    total_price: float
    user_id: UUID
    product_ids: list[UUID] = field(default_factory=list)

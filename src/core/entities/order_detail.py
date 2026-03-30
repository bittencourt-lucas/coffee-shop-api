from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.core.enums import OrderStatus
from src.core.entities.order_item import OrderItem


@dataclass
class OrderDetail:
    id: UUID
    status: OrderStatus
    total_price: float
    created_at: datetime
    items: list[OrderItem] = field(default_factory=list)

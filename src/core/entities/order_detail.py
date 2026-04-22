from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.core.enums import OrderStatus
from src.core.entities.order_item import OrderItem


@dataclass
class OrderDetail:
    id: UUID
    status: OrderStatus
    total_price: Decimal
    created_at: datetime
    items: list[OrderItem] = field(default_factory=list)

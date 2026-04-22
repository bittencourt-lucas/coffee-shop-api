from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from src.core.enums import OrderStatus


@dataclass
class Order:
    id: UUID
    status: OrderStatus
    total_price: Decimal
    user_id: UUID
    product_ids: list[UUID] = field(default_factory=list)

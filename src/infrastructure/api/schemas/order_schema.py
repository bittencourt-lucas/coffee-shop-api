from uuid import UUID

from pydantic import BaseModel

from src.core.enums import OrderStatus


class OrderCreate(BaseModel):
    product_ids: list[UUID]
    total_price: float


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_price: float
    product_ids: list[UUID]

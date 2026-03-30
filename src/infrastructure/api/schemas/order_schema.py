from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.enums import OrderStatus


class OrderCreate(BaseModel):
    product_ids: list[UUID] = Field(..., min_length=1, max_length=50)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_price: float
    product_ids: list[UUID]


class OrderItemResponse(BaseModel):
    id: UUID
    name: str
    variation: str
    unit_price: float


class OrderDetailResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_price: float
    created_at: datetime
    items: list[OrderItemResponse]

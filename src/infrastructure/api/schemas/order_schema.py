from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, PlainSerializer

from src.core.enums import OrderStatus

_MoneyDecimal = Annotated[Decimal, PlainSerializer(lambda v: str(v.quantize(Decimal("0.01"))))]


class OrderCreate(BaseModel):
    product_ids: list[UUID] = Field(..., min_length=1, max_length=50)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_price: _MoneyDecimal
    user_id: UUID
    product_ids: list[UUID]


class OrderItemResponse(BaseModel):
    id: UUID
    name: str
    variation: str
    unit_price: _MoneyDecimal


class OrderDetailResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_price: _MoneyDecimal
    created_at: datetime
    items: list[OrderItemResponse]


class PaginatedOrderResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int

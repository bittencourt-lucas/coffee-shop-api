from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, PlainSerializer

_MoneyDecimal = Annotated[Decimal, PlainSerializer(lambda v: str(v.quantize(Decimal("0.01"))))]


class MenuVariationResponse(BaseModel):
    id: UUID
    variation: str
    unit_price: _MoneyDecimal


class MenuItemResponse(BaseModel):
    name: str
    base_price: _MoneyDecimal
    variations: list[MenuVariationResponse]


class PaginatedMenuResponse(BaseModel):
    items: list[MenuItemResponse]
    total: int
    page: int
    page_size: int

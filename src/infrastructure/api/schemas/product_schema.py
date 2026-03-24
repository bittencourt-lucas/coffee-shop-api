from uuid import UUID

from pydantic import BaseModel


class MenuVariationResponse(BaseModel):
    variation: str
    price_change: float


class MenuItemResponse(BaseModel):
    name: str
    base_price: float
    variations: list[MenuVariationResponse]


class ProductCreate(BaseModel):
    name: str
    base_price: float
    variation: str
    price_change: float


class ProductUpdate(BaseModel):
    name: str
    base_price: float
    variation: str
    price_change: float


class ProductResponse(BaseModel):
    id: UUID
    name: str
    base_price: float
    variation: str
    price_change: float

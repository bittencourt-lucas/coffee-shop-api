from uuid import UUID

from pydantic import BaseModel


class MenuVariationResponse(BaseModel):
    id: UUID
    variation: str
    unit_price: float


class MenuItemResponse(BaseModel):
    name: str
    base_price: float
    variations: list[MenuVariationResponse]

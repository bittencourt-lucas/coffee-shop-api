from pydantic import BaseModel


class MenuVariationResponse(BaseModel):
    variation: str
    price_change: float


class MenuItemResponse(BaseModel):
    name: str
    base_price: float
    variations: list[MenuVariationResponse]

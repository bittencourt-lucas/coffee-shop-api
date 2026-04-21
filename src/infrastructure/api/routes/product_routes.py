from fastapi import APIRouter, Depends

from src.core.repositories import AbstractProductRepository
from src.infrastructure.api.dependencies import get_product_repository
from src.infrastructure.api.schemas import MenuItemResponse, MenuVariationResponse
from src.use_cases.product import GetMenu

menu_router = APIRouter(tags=["menu"])


@menu_router.get("/menu", response_model=list[MenuItemResponse])
async def get_menu(
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    items = await GetMenu(repo).execute()
    return [
        MenuItemResponse(
            name=item.name,
            base_price=item.base_price,
            variations=[
                MenuVariationResponse(
                    id=variation.id,
                    variation=variation.variation,
                    unit_price=variation.unit_price,
                )
                for variation in item.variations
            ],
        )
        for item in items
    ]

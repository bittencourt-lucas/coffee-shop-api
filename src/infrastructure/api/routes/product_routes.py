from fastapi import APIRouter, Depends, Query

from src.core.repositories import AbstractProductRepository
from src.infrastructure.api.dependencies import get_product_repository
from src.infrastructure.api.schemas import MenuItemResponse, MenuVariationResponse, PaginatedMenuResponse
from src.use_cases.product import GetMenu

menu_router = APIRouter(tags=["menu"])


@menu_router.get("/menu", response_model=PaginatedMenuResponse)
async def get_menu(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    offset = (page - 1) * page_size
    items, total = await GetMenu(repo).execute(offset=offset, limit=page_size)
    return PaginatedMenuResponse(
        items=[
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
        ],
        total=total,
        page=page,
        page_size=page_size,
    )

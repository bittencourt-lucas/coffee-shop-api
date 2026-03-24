from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.repositories import AbstractProductRepository
from src.infrastructure.api.dependencies import get_product_repository
from src.infrastructure.api.schemas import ProductCreate, ProductUpdate, ProductResponse, MenuItemResponse, MenuVariationResponse
from src.use_cases.product import CreateProduct, GetProduct, GetMenu, ListProducts, UpdateProduct, DeleteProduct

router = APIRouter(prefix="/products", tags=["products"])
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
                MenuVariationResponse(variation=v.variation, price_change=v.price_change)
                for v in item.variations
            ],
        )
        for item in items
    ]


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    product = await CreateProduct(repo).execute(**body.model_dump())
    return ProductResponse(**vars(product))


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    products = await ListProducts(repo).execute()
    return [ProductResponse(**vars(p)) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    product = await GetProduct(repo).execute(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse(**vars(product))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    product = await UpdateProduct(repo).execute(product_id, **body.model_dump())
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse(**vars(product))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    repo: AbstractProductRepository = Depends(get_product_repository),
):
    deleted = await DeleteProduct(repo).execute(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

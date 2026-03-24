from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.repositories import AbstractOrderRepository
from src.infrastructure.api.dependencies import get_order_repository
from src.infrastructure.api.schemas import OrderCreate, OrderStatusUpdate, OrderResponse
from src.use_cases.order import CreateOrder, GetOrder, ListOrders, UpdateOrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    repo: AbstractOrderRepository = Depends(get_order_repository),
):
    order = await CreateOrder(repo).execute(
        product_ids=body.product_ids,
        total_price=body.total_price,
    )
    return OrderResponse(**vars(order))


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    repo: AbstractOrderRepository = Depends(get_order_repository),
):
    orders = await ListOrders(repo).execute()
    return [OrderResponse(**vars(o)) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    repo: AbstractOrderRepository = Depends(get_order_repository),
):
    order = await GetOrder(repo).execute(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**vars(order))


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    body: OrderStatusUpdate,
    repo: AbstractOrderRepository = Depends(get_order_repository),
):
    order = await UpdateOrderStatus(repo).execute(order_id, body.status)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**vars(order))

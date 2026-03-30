from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.core.enums import Role
from src.core.exceptions import InvalidProductError, InvalidStatusTransitionError, PaymentFailedError
from src.core.repositories import AbstractOrderRepository, AbstractProductRepository
from src.core.services import AbstractNotificationService, AbstractPaymentService
from src.infrastructure.api.dependencies import (
    get_notification_service,
    get_order_repository,
    get_payment_service,
    get_product_repository,
    require_roles,
)
from src.infrastructure.api.schemas import (
    OrderCreate,
    OrderDetailResponse,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from src.infrastructure.api.middleware.rate_limit import limiter
from src.use_cases.order import CreateOrder, GetOrderDetail, UpdateOrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    body: OrderCreate,
    order_repo: AbstractOrderRepository = Depends(get_order_repository),
    product_repo: AbstractProductRepository = Depends(get_product_repository),
    payment_service: AbstractPaymentService = Depends(get_payment_service),
):
    try:
        order = await CreateOrder(order_repo, product_repo, payment_service).execute(
            product_ids=body.product_ids,
        )
    except InvalidProductError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    except PaymentFailedError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment could not be processed")
    return OrderResponse(**vars(order))


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: UUID,
    repo: AbstractOrderRepository = Depends(get_order_repository),
):
    order = await GetOrderDetail(repo).execute(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderDetailResponse(
        id=order.id,
        status=order.status,
        total_price=order.total_price,
        created_at=order.created_at,
        items=[OrderItemResponse(**vars(item)) for item in order.items],
    )


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    body: OrderStatusUpdate,
    repo: AbstractOrderRepository = Depends(get_order_repository),
    notification_service: AbstractNotificationService = Depends(get_notification_service),
    _: Role = Depends(require_roles(Role.MANAGER)),
):
    try:
        order = await UpdateOrderStatus(repo, notification_service).execute(order_id, body.status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**vars(order))

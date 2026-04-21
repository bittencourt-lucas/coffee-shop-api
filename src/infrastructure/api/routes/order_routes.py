from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.core.enums import Role
from src.core.exceptions import InvalidProductError, InvalidStatusTransitionError, PaymentFailedError
from src.core.repositories import AbstractOrderRepository, AbstractProductRepository, AbstractIdempotencyRepository
from src.core.services import AbstractNotificationService, AbstractPaymentService
from src.infrastructure.api.dependencies import (
    get_current_user,
    get_idempotency_repository,
    get_notification_service,
    get_order_repository,
    get_payment_service,
    get_product_repository,
    require_roles,
)
from src.infrastructure.auth.jwt import TokenData
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
    _: TokenData = Depends(get_current_user),
    order_repo: AbstractOrderRepository = Depends(get_order_repository),
    product_repo: AbstractProductRepository = Depends(get_product_repository),
    payment_service: AbstractPaymentService = Depends(get_payment_service),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    idempotency_repo: AbstractIdempotencyRepository = Depends(get_idempotency_repository),
):
    if idempotency_key:
        cached = await idempotency_repo.get(idempotency_key)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.body)

    try:
        order = await CreateOrder(order_repo, product_repo, payment_service).execute(
            product_ids=body.product_ids,
        )
    except InvalidProductError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    except PaymentFailedError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment could not be processed")

    response = OrderResponse(**vars(order))

    if idempotency_key:
        await idempotency_repo.save(idempotency_key, status.HTTP_201_CREATED, response.model_dump(mode="json"))

    return response


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: UUID,
    _: TokenData = Depends(get_current_user),
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
    _: TokenData = Depends(require_roles(Role.MANAGER)),
):
    try:
        order = await UpdateOrderStatus(repo, notification_service).execute(order_id, body.status)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse(**vars(order))

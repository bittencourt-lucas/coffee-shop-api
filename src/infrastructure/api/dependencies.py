from fastapi import HTTPException, Request, status

from src.core.enums import Role
from src.infrastructure.database.connection import database
from src.infrastructure.database.repositories import ProductRepository, OrderRepository
from src.core.repositories import AbstractProductRepository, AbstractOrderRepository
from src.core.services import AbstractPaymentService
from src.infrastructure.services import PaymentService


def get_payment_service() -> AbstractPaymentService:
    return PaymentService()


def get_product_repository() -> AbstractProductRepository:
    return ProductRepository(database)


def get_order_repository() -> AbstractOrderRepository:
    return OrderRepository(database)


def require_roles(*allowed_roles: Role):
    def dependency(request: Request) -> Role:
        role: Role = request.state.role
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role.value}' is not allowed to access this resource.",
            )
        return role
    return dependency

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.enums import Role
from src.core.exceptions import InvalidCredentialsError
from src.core.repositories import (
    AbstractProductRepository,
    AbstractOrderRepository,
    AbstractUserRepository,
    AbstractIdempotencyRepository,
    AbstractRevokedTokenRepository,
)
from src.core.services import AbstractPaymentService, AbstractNotificationService
from src.infrastructure.auth.jwt import TokenData, decode_access_token
from src.infrastructure.database.connection import database
from src.infrastructure.database.repositories import (
    ProductRepository,
    OrderRepository,
    UserRepository,
    IdempotencyRepository,
    RevokedTokenRepository,
)
from src.infrastructure.redis_client import redis_client
from src.infrastructure.services import PaymentService, RedisNotificationService

_bearer = HTTPBearer(auto_error=False)


def get_payment_service() -> AbstractPaymentService:
    return PaymentService()


def get_notification_service() -> AbstractNotificationService:
    return RedisNotificationService(redis_client)


def get_product_repository() -> AbstractProductRepository:
    return ProductRepository(database)


def get_order_repository() -> AbstractOrderRepository:
    return OrderRepository(database)


def get_user_repository() -> AbstractUserRepository:
    return UserRepository(database)


def get_idempotency_repository() -> AbstractIdempotencyRepository:
    return IdempotencyRepository(database)


def get_revoked_token_repository() -> AbstractRevokedTokenRepository:
    return RevokedTokenRepository(database)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    revoked_repo: AbstractRevokedTokenRepository = Depends(get_revoked_token_repository),
) -> TokenData:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    try:
        token_data = decode_access_token(credentials.credentials)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    if await revoked_repo.is_revoked(token_data.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")
    return token_data


def require_roles(*allowed_roles: Role):
    def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not allowed to access this resource.",
            )
        return current_user
    return dependency

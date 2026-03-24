from fastapi import Depends

from src.infrastructure.database.connection import database
from src.infrastructure.database.repositories import (
    ProductRepository,
    UserRepository,
    OrderRepository,
)
from src.core.repositories import (
    AbstractProductRepository,
    AbstractUserRepository,
    AbstractOrderRepository,
)


def get_product_repository() -> AbstractProductRepository:
    return ProductRepository(database)


def get_user_repository() -> AbstractUserRepository:
    return UserRepository(database)


def get_order_repository() -> AbstractOrderRepository:
    return OrderRepository(database)

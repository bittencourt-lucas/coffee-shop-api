from .product_routes import menu_router
from .order_routes import router as order_router
from .healthcheck_routes import router as healthcheck_router
from .user_routes import router as user_router
from .auth_routes import router as auth_router

__all__ = ["menu_router", "order_router", "healthcheck_router", "user_router", "auth_router"]

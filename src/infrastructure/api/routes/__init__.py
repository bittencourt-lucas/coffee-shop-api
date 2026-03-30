from .product_routes import menu_router
from .order_routes import router as order_router
from .healthcheck_routes import router as healthcheck_router

__all__ = ["menu_router", "order_router", "healthcheck_router"]

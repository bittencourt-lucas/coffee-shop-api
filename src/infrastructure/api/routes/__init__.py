from .product_routes import menu_router
from .user_routes import router as user_router
from .order_routes import router as order_router

__all__ = ["menu_router", "user_router", "order_router"]

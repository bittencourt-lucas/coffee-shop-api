from .product_routes import router as product_router
from .user_routes import router as user_router
from .order_routes import router as order_router

__all__ = ["product_router", "user_router", "order_router"]

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.infrastructure.api.middleware.rate_limit import limiter
from src.infrastructure.api.middleware.role_middleware import RoleMiddleware
from src.infrastructure.database.connection import database
from src.infrastructure.database.repositories import IdempotencyRepository, RevokedTokenRepository
from src.infrastructure.database.seed import seed_catalog
from src.infrastructure.api.routes import menu_router, order_router, healthcheck_router, user_router, auth_router
from src.infrastructure.redis_client import redis_client
from src.infrastructure.settings import settings
from src.infrastructure.tasks.notification_worker import notification_worker
from src.infrastructure.tasks.purge_expired import purge_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await seed_catalog(database)
    purge_task = asyncio.create_task(
        purge_loop(IdempotencyRepository(database), RevokedTokenRepository(database))
    )
    notification_task = asyncio.create_task(
        notification_worker(redis_client, settings.notification_url)
    )
    yield
    purge_task.cancel()
    notification_task.cancel()
    try:
        await purge_task
    except asyncio.CancelledError:
        pass
    try:
        await notification_task
    except asyncio.CancelledError:
        pass
    await database.disconnect()
    await redis_client.aclose()


app = FastAPI(title="Coffee Shop API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RoleMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["X-Role", "Content-Type", "Idempotency-Key", "Authorization"],
)

app.include_router(healthcheck_router)
app.include_router(menu_router)
app.include_router(order_router)
app.include_router(user_router)
app.include_router(auth_router)

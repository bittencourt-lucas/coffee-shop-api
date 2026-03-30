from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.api.middleware.role_middleware import RoleMiddleware
from src.infrastructure.database.connection import database
from src.infrastructure.database.seed import seed_catalog
from src.infrastructure.api.routes import menu_router, order_router, healthcheck_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await seed_catalog(database)
    yield
    await database.disconnect()


app = FastAPI(title="Coffee Shop API", lifespan=lifespan)

app.add_middleware(RoleMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["X-Role", "Content-Type"],
)

app.include_router(healthcheck_router)
app.include_router(menu_router)
app.include_router(order_router)

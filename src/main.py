from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.database.connection import database
from src.infrastructure.database.seed import seed_catalog
from src.infrastructure.api.routes import menu_router, user_router, order_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await seed_catalog(database)
    yield
    await database.disconnect()


app = FastAPI(title="Coffee Shop API", lifespan=lifespan)

app.include_router(menu_router)
app.include_router(user_router)
app.include_router(order_router)

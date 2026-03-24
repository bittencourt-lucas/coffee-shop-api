from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.database.connection import database
from src.infrastructure.api.routes import product_router, user_router, order_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(title="Coffee Shop API", lifespan=lifespan)

app.include_router(product_router)
app.include_router(user_router)
app.include_router(order_router)

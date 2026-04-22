import redis.asyncio as aioredis

from src.core.services import AbstractNotificationService

STREAM_NAME = "notifications"


class RedisNotificationService(AbstractNotificationService):
    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def notify(self, status: str) -> None:
        await self._redis.xadd(STREAM_NAME, {"status": status})

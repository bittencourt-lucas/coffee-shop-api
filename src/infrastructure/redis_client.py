import redis.asyncio as aioredis

from src.infrastructure.settings import settings

redis_client = aioredis.Redis.from_url(settings.redis_url, decode_responses=True)

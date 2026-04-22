import asyncio
import logging

import httpx
import redis.asyncio as aioredis
from redis import ResponseError

logger = logging.getLogger(__name__)

STREAM_NAME = "notifications"
GROUP_NAME = "notification-group"
CONSUMER_NAME = "worker-1"
MAX_RETRIES = 3
CLAIM_IDLE_MS = 60_000


async def notification_worker(redis_client: aioredis.Redis, notification_url: str) -> None:
    try:
        await redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        logger.debug("Consumer group '%s' already exists.", GROUP_NAME)

    while True:
        try:
            await _process_batch(redis_client, notification_url)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected error in notification worker; retrying in 1s.")
            await asyncio.sleep(1)


async def _process_batch(redis_client: aioredis.Redis, notification_url: str) -> None:
    next_id, claimed, _ = await redis_client.xautoclaim(
        STREAM_NAME, GROUP_NAME, CONSUMER_NAME,
        min_idle_time=CLAIM_IDLE_MS, start_id="0-0", count=10,
    )
    for msg_id, fields in claimed:
        await _deliver(redis_client, notification_url, msg_id, fields)

    result = await redis_client.xreadgroup(
        GROUP_NAME, CONSUMER_NAME,
        {STREAM_NAME: ">"},
        count=10, block=5000,
    )
    if result:
        for msg_id, fields in result[0][1]:
            await _deliver(redis_client, notification_url, msg_id, fields)


async def _deliver(
    redis_client: aioredis.Redis,
    notification_url: str,
    msg_id: str,
    fields: dict,
) -> None:
    status = fields.get("status", "")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.post(notification_url, json={"status": status})
            if response.is_success:
                await redis_client.xack(STREAM_NAME, GROUP_NAME, msg_id)
                logger.info("Notification delivered for message %s", msg_id)
                return
            logger.warning(
                "Attempt %d/%d — HTTP %d for message %s",
                attempt, MAX_RETRIES, response.status_code, msg_id,
            )
        except httpx.RequestError as exc:
            logger.warning(
                "Attempt %d/%d — Request error for message %s: %s",
                attempt, MAX_RETRIES, msg_id, exc,
            )
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)

    logger.error(
        "Notification failed after %d attempts for message %s; acknowledging to prevent requeue.",
        MAX_RETRIES, msg_id,
    )
    await redis_client.xack(STREAM_NAME, GROUP_NAME, msg_id)

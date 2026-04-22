from unittest.mock import AsyncMock

from src.infrastructure.services.redis_notification_service import RedisNotificationService, STREAM_NAME


async def test_notify_publishes_status_to_stream():
    redis = AsyncMock()
    service = RedisNotificationService(redis)
    await service.notify("READY")
    redis.xadd.assert_awaited_once_with(STREAM_NAME, {"status": "READY"})


async def test_notify_does_not_make_http_call():
    redis = AsyncMock()
    service = RedisNotificationService(redis)
    await service.notify("PREPARATION")
    redis.xadd.assert_awaited_once()


async def test_notify_publishes_each_call_independently():
    redis = AsyncMock()
    service = RedisNotificationService(redis)
    await service.notify("WAITING")
    await service.notify("PREPARATION")
    assert redis.xadd.await_count == 2
    redis.xadd.assert_any_await(STREAM_NAME, {"status": "WAITING"})
    redis.xadd.assert_any_await(STREAM_NAME, {"status": "PREPARATION"})


async def test_notify_propagates_redis_error():
    redis = AsyncMock()
    redis.xadd.side_effect = ConnectionError("Redis unavailable")
    service = RedisNotificationService(redis)
    try:
        await service.notify("READY")
        assert False, "Expected ConnectionError"
    except ConnectionError:
        pass

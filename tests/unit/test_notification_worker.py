from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.infrastructure.tasks.notification_worker import (
    _deliver,
    GROUP_NAME,
    MAX_RETRIES,
    STREAM_NAME,
)

_NOTIFY_URL = "http://test/notify"


def _mock_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    return resp


def _mock_http_client(*responses):
    mock_cm = MagicMock()
    mock_inner = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_inner)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    mock_inner.post.side_effect = list(responses)
    return mock_cm, mock_inner


async def test_deliver_sends_correct_payload_and_acks():
    redis = AsyncMock()
    mock_cm, mock_inner = _mock_http_client(_mock_response(200))
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    mock_inner.post.assert_awaited_once_with(_NOTIFY_URL, json={"status": "READY"})
    redis.xack.assert_awaited_once_with(STREAM_NAME, GROUP_NAME, "1-0")


async def test_deliver_does_not_retry_on_first_success():
    redis = AsyncMock()
    mock_cm, mock_inner = _mock_http_client(_mock_response(200))
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    assert mock_inner.post.await_count == 1


async def test_deliver_retries_and_succeeds_on_second_attempt():
    redis = AsyncMock()
    mock_cm, mock_inner = _mock_http_client(_mock_response(500), _mock_response(200))
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", new_callable=AsyncMock):
            await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    assert mock_inner.post.await_count == 2
    redis.xack.assert_awaited_once_with(STREAM_NAME, GROUP_NAME, "1-0")


async def test_deliver_exhausts_max_retries_on_non_2xx():
    redis = AsyncMock()
    mock_cm, mock_inner = _mock_http_client(*[_mock_response(503)] * MAX_RETRIES)
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", new_callable=AsyncMock):
            await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    assert mock_inner.post.await_count == MAX_RETRIES


async def test_deliver_acks_after_exhausting_retries():
    redis = AsyncMock()
    mock_cm, _ = _mock_http_client(*[_mock_response(503)] * MAX_RETRIES)
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", new_callable=AsyncMock):
            await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    redis.xack.assert_awaited_once_with(STREAM_NAME, GROUP_NAME, "1-0")


async def test_deliver_retries_on_request_error_then_acks():
    redis = AsyncMock()
    error = httpx.ConnectError("refused")
    mock_cm, mock_inner = _mock_http_client(*[error] * MAX_RETRIES)
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", new_callable=AsyncMock):
            await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    assert mock_inner.post.await_count == MAX_RETRIES
    redis.xack.assert_awaited_once_with(STREAM_NAME, GROUP_NAME, "1-0")


async def test_deliver_uses_exponential_backoff():
    redis = AsyncMock()
    mock_cm, _ = _mock_http_client(*[_mock_response(500)] * MAX_RETRIES)
    sleep_mock = AsyncMock()
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", sleep_mock):
            await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    sleep_calls = [call.args[0] for call in sleep_mock.await_args_list]
    assert sleep_calls == [2, 4]  # 2^1, 2^2 — no sleep after last attempt


async def test_deliver_logs_error_after_exhausting_retries(caplog):
    redis = AsyncMock()
    mock_cm, _ = _mock_http_client(*[_mock_response(503)] * MAX_RETRIES)
    with patch("src.infrastructure.tasks.notification_worker.httpx.AsyncClient", return_value=mock_cm):
        with patch("src.infrastructure.tasks.notification_worker.asyncio.sleep", new_callable=AsyncMock):
            with caplog.at_level("ERROR"):
                await _deliver(redis, _NOTIFY_URL, "1-0", {"status": "READY"})
    assert "failed after" in caplog.text.lower()

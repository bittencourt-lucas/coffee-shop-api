import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.exceptions import PaymentFailedError
from src.infrastructure.services.payment_service import PaymentService


_SUCCESS_DATA = {"id": "pay-123", "status": "approved"}
_FAILURE_DATA = {"error": "declined"}


@pytest.fixture(autouse=True)
async def bypass_circuit_breaker():
    async def passthrough(coro):
        return await coro

    with patch(
        "src.infrastructure.services.payment_service.payment_circuit_breaker.call",
        side_effect=passthrough,
    ):
        yield


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    async def instant(_):
        pass

    monkeypatch.setattr("tenacity.nap.sleep", instant)


def _make_response(status_code: int, data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.json.return_value = data
    return resp


def _patch_client(*responses):
    mock_cm = MagicMock()
    mock_inner = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_inner)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    mock_inner.post.side_effect = list(responses)

    patcher = patch(
        "src.infrastructure.services.payment_service.httpx.AsyncClient",
        return_value=mock_cm,
    )
    return patcher, mock_inner


async def test_returns_response_data_on_success():
    patcher, _ = _patch_client(_make_response(200, _SUCCESS_DATA))
    with patcher:
        result = await PaymentService().process(19.90)
    assert result == _SUCCESS_DATA


async def test_logs_full_response(caplog):
    patcher, _ = _patch_client(_make_response(200, _SUCCESS_DATA))
    with patcher, caplog.at_level("INFO"):
        await PaymentService().process(19.90)
    assert "200" in caplog.text
    assert str(_SUCCESS_DATA) in caplog.text


async def test_does_not_retry_on_first_success():
    patcher, mock_inner = _patch_client(_make_response(200, _SUCCESS_DATA))
    with patcher:
        await PaymentService().process(19.90)
    assert mock_inner.post.call_count == 1


async def test_succeeds_on_second_attempt_after_first_fails():
    patcher, mock_inner = _patch_client(
        _make_response(500, _FAILURE_DATA),
        _make_response(200, _SUCCESS_DATA),
    )
    with patcher:
        result = await PaymentService().process(19.90)
    assert result == _SUCCESS_DATA
    assert mock_inner.post.call_count == 2


async def test_succeeds_on_third_attempt_after_two_failures():
    patcher, mock_inner = _patch_client(
        _make_response(500, _FAILURE_DATA),
        _make_response(500, _FAILURE_DATA),
        _make_response(200, _SUCCESS_DATA),
    )
    with patcher:
        result = await PaymentService().process(19.90)
    assert result == _SUCCESS_DATA
    assert mock_inner.post.call_count == 3


async def test_retries_exactly_three_times_on_non_2xx():
    patcher, mock_inner = _patch_client(
        _make_response(503, _FAILURE_DATA),
        _make_response(503, _FAILURE_DATA),
        _make_response(503, _FAILURE_DATA),
    )
    with patcher:
        with pytest.raises(PaymentFailedError):
            await PaymentService().process(19.90)
    assert mock_inner.post.call_count == 3


async def test_raises_payment_failed_error_after_all_non_2xx_retries():
    patcher, _ = _patch_client(
        _make_response(500, _FAILURE_DATA),
        _make_response(500, _FAILURE_DATA),
        _make_response(500, _FAILURE_DATA),
    )
    with patcher:
        with pytest.raises(PaymentFailedError):
            await PaymentService().process(19.90)


async def test_raises_payment_failed_error_after_all_request_errors():
    error = httpx.ConnectError("connection refused")
    patcher, _ = _patch_client(error, error, error)
    with patcher:
        with pytest.raises(PaymentFailedError):
            await PaymentService().process(19.90)


async def test_retries_exactly_three_times_on_request_error():
    error = httpx.ConnectError("timeout")
    patcher, mock_inner = _patch_client(error, error, error)
    with patcher:
        with pytest.raises(PaymentFailedError):
            await PaymentService().process(19.90)
    assert mock_inner.post.call_count == 3


async def test_logs_each_failed_attempt(caplog):
    patcher, _ = _patch_client(
        _make_response(500, _FAILURE_DATA),
        _make_response(500, _FAILURE_DATA),
        _make_response(200, _SUCCESS_DATA),
    )
    with patcher, caplog.at_level("INFO"):
        await PaymentService().process(19.90)
    assert "1/3" in caplog.text
    assert "2/3" in caplog.text


async def test_circuit_open_raises_payment_failed_error():
    with patch(
        "src.infrastructure.services.payment_service.payment_circuit_breaker.call",
        side_effect=PaymentFailedError("Circuit breaker is OPEN — failing fast"),
    ):
        with pytest.raises(PaymentFailedError, match="OPEN"):
            await PaymentService().process(19.90)

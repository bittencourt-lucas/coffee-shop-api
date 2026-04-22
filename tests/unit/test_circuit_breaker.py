import pytest
from unittest.mock import patch

from src.core.exceptions import PaymentFailedError
from src.infrastructure.services.circuit_breaker import CircuitBreaker, CircuitState


async def _fail():
    raise ValueError("fail")


async def _succeed():
    return "ok"


async def test_initial_state_is_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    assert cb.state == CircuitState.CLOSED


async def test_single_failure_does_not_open_circuit():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    with pytest.raises(ValueError):
        await cb.call(_fail())
    assert cb.state == CircuitState.CLOSED


async def test_closed_to_open_on_threshold_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    for _ in range(3):
        with pytest.raises(ValueError):
            await cb.call(_fail())
    assert cb.state == CircuitState.OPEN


async def test_open_raises_immediately_without_awaiting_coro():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)
    with pytest.raises(ValueError):
        await cb.call(_fail())
    assert cb.state == CircuitState.OPEN

    called = False

    async def probe():
        nonlocal called
        called = True
        return "ok"

    with pytest.raises(PaymentFailedError, match="OPEN"):
        await cb.call(probe())

    assert not called


async def test_open_transitions_to_half_open_after_recovery_timeout():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=100.0):
        with pytest.raises(ValueError):
            await cb.call(_fail())

    assert cb.state == CircuitState.OPEN
    assert cb._opened_at == 100.0

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=131.0):
        result = await cb.call(_succeed())

    assert result == "ok"
    assert cb.state == CircuitState.CLOSED


async def test_half_open_probe_success_transitions_to_closed():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=0.0):
        with pytest.raises(ValueError):
            await cb.call(_fail())

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=31.0):
        await cb.call(_succeed())

    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0
    assert cb._opened_at is None


async def test_half_open_probe_failure_transitions_back_to_open():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=0.0):
        with pytest.raises(ValueError):
            await cb.call(_fail())

    with patch("src.infrastructure.services.circuit_breaker.time.monotonic", return_value=31.0):
        with pytest.raises(ValueError):
            await cb.call(_fail())

    assert cb.state == CircuitState.OPEN


async def test_failure_count_resets_after_success():
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)

    for _ in range(4):
        with pytest.raises(ValueError):
            await cb.call(_fail())

    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 4

    await cb.call(_succeed())

    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0


async def test_success_on_closed_circuit_returns_result():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    result = await cb.call(_succeed())
    assert result == "ok"

import asyncio
import logging
import time
from enum import Enum

from src.core.exceptions import PaymentFailedError
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(self, coro):
        async with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._opened_at
                if elapsed >= self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker: OPEN → HALF_OPEN (probe allowed)")
                else:
                    coro.close()
                    raise PaymentFailedError("Circuit breaker is OPEN — failing fast")

        try:
            result = await coro
        except Exception:
            await self._on_failure()
            raise

        await self._on_success()
        return result

    async def _on_success(self):
        async with self._lock:
            prev = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._opened_at = None
            if prev == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (probe succeeded)")

    async def _on_failure(self):
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.warning("Circuit breaker: HALF_OPEN → OPEN (probe failed)")
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.monotonic()
                    logger.warning(
                        "Circuit breaker: CLOSED → OPEN after %d consecutive failures",
                        self._failure_count,
                    )


payment_circuit_breaker = CircuitBreaker(
    failure_threshold=settings.payment_circuit_breaker_threshold,
    recovery_timeout=settings.payment_circuit_breaker_recovery_seconds,
)

import logging

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from src.core.exceptions import PaymentFailedError
from src.core.services import AbstractPaymentService
from src.infrastructure.services.circuit_breaker import payment_circuit_breaker
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


class _NonSuccessResponse(Exception):
    pass


def _log_retry(retry_state: RetryCallState) -> None:
    logger.warning(
        "Payment attempt %d/%d failed: %s",
        retry_state.attempt_number,
        MAX_RETRIES,
        retry_state.outcome.exception(),
    )


class PaymentService(AbstractPaymentService):
    @retry(
        retry=retry_if_exception_type((httpx.RequestError, _NonSuccessResponse)),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential_jitter(initial=1, max=10),
        before_sleep=_log_retry,
        reraise=True,
    )
    async def _attempt(self, value: float) -> dict:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.post(settings.payment_url, json={"value": value})

        data = response.json()
        logger.info("HTTP %d: %s", response.status_code, data)

        if not response.is_success:
            raise _NonSuccessResponse(str(data))

        return data

    async def process(self, value: float) -> dict:
        try:
            return await payment_circuit_breaker.call(self._attempt(value))
        except PaymentFailedError:
            raise
        except Exception as exc:
            raise PaymentFailedError(str(exc)) from exc

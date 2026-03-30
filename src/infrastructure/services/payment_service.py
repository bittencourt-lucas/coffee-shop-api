import logging

import httpx

from src.core.exceptions import PaymentFailedError
from src.core.services import AbstractPaymentService
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


class PaymentService(AbstractPaymentService):
    async def process(self, value: float) -> dict:
        last_error: str = "Unknown error"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                    response = await client.post(settings.payment_url, json={"value": value})

                data = response.json()
                logger.info("Attempt %d/%d — HTTP %d: %s", attempt, MAX_RETRIES, response.status_code, data)

                if response.is_success:
                    return data

                last_error = str(data)

            except httpx.RequestError as exc:
                last_error = str(exc)
                logger.error("Attempt %d/%d — Request error: %s", attempt, MAX_RETRIES, exc)

        raise PaymentFailedError(last_error)

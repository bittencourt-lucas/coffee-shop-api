import httpx

from src.core.exceptions import PaymentFailedError
from src.core.services import AbstractPaymentService

PAYMENT_URL = "https://challenge.trio.dev/api/v1/payment"
MAX_RETRIES = 3


class PaymentService(AbstractPaymentService):
    async def process(self, value: float) -> dict:
        last_error: str = "Unknown error"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(PAYMENT_URL, json={"value": value})

                data = response.json()
                print(f"[Payment] Attempt {attempt}/{MAX_RETRIES} — HTTP {response.status_code}: {data}")

                if response.is_success:
                    return data

                last_error = str(data)

            except httpx.RequestError as exc:
                last_error = str(exc)
                print(f"[Payment] Attempt {attempt}/{MAX_RETRIES} — Request error: {exc}")

        raise PaymentFailedError(last_error)

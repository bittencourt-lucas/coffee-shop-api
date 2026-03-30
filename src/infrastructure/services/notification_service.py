import asyncio
import logging

import httpx

from src.core.services import AbstractNotificationService
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)


class NotificationService(AbstractNotificationService):
    async def notify(self, status: str) -> None:
        asyncio.create_task(self._send(status))

    @staticmethod
    async def _send(status: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                response = await client.post(settings.notification_url, json={"status": status})
            logger.info("HTTP %d: %s", response.status_code, response.json())
        except Exception as exc:
            logger.error("Failed: %s", exc)

import asyncio

import httpx

from src.core.services import AbstractNotificationService

NOTIFICATION_URL = "https://challenge.trio.dev/api/v1/notification"


class NotificationService(AbstractNotificationService):
    async def notify(self, status: str) -> None:
        asyncio.create_task(self._send(status))

    @staticmethod
    async def _send(status: str) -> None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(NOTIFICATION_URL, json={"status": status})
            print(f"[Notification] HTTP {response.status_code}: {response.json()}")
        except Exception as exc:
            print(f"[Notification] Failed: {exc}")

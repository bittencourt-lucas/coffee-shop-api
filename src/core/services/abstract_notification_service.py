from abc import ABC, abstractmethod


class AbstractNotificationService(ABC):
    @abstractmethod
    async def notify(self, status: str) -> None:
        ...

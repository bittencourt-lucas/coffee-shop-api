from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta

IDEMPOTENCY_TTL = timedelta(hours=24)


@dataclass
class CachedResponse:
    status_code: int
    body: dict


class AbstractIdempotencyRepository(ABC):
    @abstractmethod
    async def get(self, key: str) -> CachedResponse | None:
        pass

    @abstractmethod
    async def save(self, key: str, status_code: int, body: dict) -> None:
        pass

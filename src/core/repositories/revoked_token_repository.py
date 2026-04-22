from abc import ABC, abstractmethod
from datetime import datetime


class AbstractRevokedTokenRepository(ABC):
    @abstractmethod
    async def revoke(self, jti: str, expires_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_revoked(self, jti: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete_expired(self) -> None:
        raise NotImplementedError

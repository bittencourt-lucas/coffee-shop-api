from datetime import datetime, timezone

import databases

from src.core.repositories.revoked_token_repository import AbstractRevokedTokenRepository
from src.infrastructure.database.models.revoked_token_model import revoked_tokens_table


class RevokedTokenRepository(AbstractRevokedTokenRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        await self._db.execute(
            revoked_tokens_table.insert().values(
                jti=jti,
                expires_at=expires_at.replace(tzinfo=None),
            )
        )

    async def is_revoked(self, jti: str) -> bool:
        row = await self._db.fetch_one(
            revoked_tokens_table.select().where(revoked_tokens_table.c.jti == jti)
        )
        return row is not None

    async def delete_expired(self) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self._db.execute(
            revoked_tokens_table.delete().where(revoked_tokens_table.c.expires_at < now)
        )

import json
from datetime import datetime, timezone

import databases

from src.core.repositories.idempotency_repository import (
    AbstractIdempotencyRepository,
    CachedResponse,
    IDEMPOTENCY_TTL,
)
from src.infrastructure.database.models.idempotency_model import idempotency_keys_table


class IdempotencyRepository(AbstractIdempotencyRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def get(self, key: str) -> CachedResponse | None:
        row = await self._db.fetch_one(
            idempotency_keys_table.select().where(idempotency_keys_table.c.key == key)
        )
        if not row:
            return None
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - IDEMPOTENCY_TTL
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at < cutoff:
            return None
        return CachedResponse(
            status_code=row["status_code"],
            body=json.loads(row["response_body"]),
        )

    async def save(self, key: str, status_code: int, body: dict) -> None:
        await self._db.execute(
            idempotency_keys_table.insert().values(
                key=key,
                status_code=status_code,
                response_body=json.dumps(body),
            )
        )

    async def delete_expired(self) -> None:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - IDEMPOTENCY_TTL
        await self._db.execute(
            idempotency_keys_table.delete().where(idempotency_keys_table.c.created_at < cutoff)
        )

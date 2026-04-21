import asyncio
import logging

from src.core.repositories.idempotency_repository import AbstractIdempotencyRepository
from src.core.repositories.revoked_token_repository import AbstractRevokedTokenRepository

logger = logging.getLogger(__name__)

PURGE_INTERVAL_SECONDS = 3600


async def purge_loop(
    idempotency_repo: AbstractIdempotencyRepository,
    revoked_token_repo: AbstractRevokedTokenRepository,
) -> None:
    while True:
        await asyncio.sleep(PURGE_INTERVAL_SECONDS)
        try:
            await idempotency_repo.delete_expired()
            await revoked_token_repo.delete_expired()
            logger.info("Purged expired idempotency keys and revoked tokens.")
        except Exception:
            logger.exception("Error during expired record purge.")

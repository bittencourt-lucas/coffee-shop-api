import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./coffee_shop.db"
    payment_url: str = "https://challenge.trio.dev/api/v1/payment"
    notification_url: str = "https://challenge.trio.dev/api/v1/notification"
    redis_url: str = "redis://localhost:6379"
    jwt_secret_key: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    model_config = {"env_prefix": "COFFEE_SHOP_"}

    @model_validator(mode="after")
    def warn_default_jwt_secret(self) -> "Settings":
        if self.jwt_secret_key == _DEFAULT_JWT_SECRET:
            logger.critical(
                "COFFEE_SHOP_JWT_SECRET_KEY is using the default value. "
                "Set a strong secret in production via the COFFEE_SHOP_JWT_SECRET_KEY env var."
            )
        return self


settings = Settings()

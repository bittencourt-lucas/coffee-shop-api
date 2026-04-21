from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./coffee_shop.db"
    payment_url: str = "https://challenge.trio.dev/api/v1/payment"
    notification_url: str = "https://challenge.trio.dev/api/v1/notification"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    model_config = {"env_prefix": "COFFEE_SHOP_"}


settings = Settings()

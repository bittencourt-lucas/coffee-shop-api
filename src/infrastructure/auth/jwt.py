from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt

from src.core.enums import Role
from src.infrastructure.settings import settings


def create_access_token(user_id: UUID, role: Role) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": str(user_id), "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

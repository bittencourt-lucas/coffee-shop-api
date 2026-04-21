from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.core.enums import Role
from src.core.exceptions import InvalidCredentialsError
from src.infrastructure.settings import settings


@dataclass
class TokenData:
    user_id: UUID
    role: Role
    jti: str
    expires_at: datetime


def create_access_token(user_id: UUID, role: Role) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": expire,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenData(
            user_id=UUID(payload["sub"]),
            role=Role(payload["role"]),
            jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except (JWTError, KeyError, ValueError):
        raise InvalidCredentialsError()

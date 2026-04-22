from src.core.exceptions import InvalidCredentialsError
from src.core.repositories import AbstractUserRepository
from src.infrastructure.auth.jwt import create_access_token
from src.infrastructure.auth.password import DUMMY_HASH, verify_password


class SignIn:
    def __init__(self, repository: AbstractUserRepository) -> None:
        self._repository = repository

    async def execute(self, email: str, password: str) -> str:
        user = await self._repository.get_by_email(email)
        hash_to_check = user.password_hash if user else DUMMY_HASH
        if not verify_password(password, hash_to_check) or not user:
            raise InvalidCredentialsError()
        return create_access_token(user.id, user.role)

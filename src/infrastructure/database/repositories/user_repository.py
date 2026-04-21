from uuid import UUID

import databases

from src.core.entities import User
from src.core.enums import Role
from src.core.repositories import AbstractUserRepository
from src.infrastructure.database.models import users_table


class UserRepository(AbstractUserRepository):
    def __init__(self, db: databases.Database) -> None:
        self._db = db

    async def create(self, user: User) -> User:
        await self._db.execute(
            users_table.insert().values(
                id=str(user.id),
                email=user.email,
                role=user.role.value,
            )
        )
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        row = await self._db.fetch_one(
            users_table.select().where(users_table.c.id == str(user_id))
        )
        if not row:
            return None
        return self._to_entity(row)

    async def list_all(self) -> list[User]:
        rows = await self._db.fetch_all(users_table.select())
        return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_entity(row) -> User:
        return User(
            id=UUID(row["id"]),
            email=row["email"],
            role=Role(row["role"]),
        )

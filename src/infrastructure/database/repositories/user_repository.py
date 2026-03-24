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
        query = users_table.insert().values(
            id=str(user.id),
            role=user.role.value,
        )
        await self._db.execute(query)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = users_table.select().where(users_table.c.id == str(user_id))
        row = await self._db.fetch_one(query)
        return self._to_entity(row) if row else None

    async def list_all(self) -> list[User]:
        query = users_table.select()
        rows = await self._db.fetch_all(query)
        return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_entity(row) -> User:
        return User(
            id=UUID(row["id"]),
            role=Role(row["role"]),
        )

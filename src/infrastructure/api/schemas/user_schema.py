from uuid import UUID

from pydantic import BaseModel

from src.core.enums import Role


class UserCreate(BaseModel):
    role: Role


class UserResponse(BaseModel):
    id: UUID
    role: Role

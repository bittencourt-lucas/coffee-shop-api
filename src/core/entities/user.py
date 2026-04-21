import uuid
from dataclasses import dataclass

from src.core.enums.role import Role


@dataclass
class User:
    id: uuid.UUID
    email: str
    role: Role
    password_hash: str

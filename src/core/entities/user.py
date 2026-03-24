from dataclasses import dataclass
from uuid import UUID

from src.core.enums import Role


@dataclass
class User:
    id: UUID
    role: Role

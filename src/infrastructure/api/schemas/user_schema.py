from uuid import UUID

from pydantic import BaseModel, EmailStr

from src.core.enums import Role


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: Role


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.repositories import AbstractUserRepository
from src.infrastructure.api.dependencies import get_user_repository
from src.infrastructure.api.schemas import UserCreate, UserResponse
from src.use_cases.user import CreateUser, GetUser, ListUsers

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    repo: AbstractUserRepository = Depends(get_user_repository),
):
    user = await CreateUser(repo).execute(role=body.role)
    return UserResponse(**vars(user))


@router.get("/", response_model=list[UserResponse])
async def list_users(
    repo: AbstractUserRepository = Depends(get_user_repository),
):
    users = await ListUsers(repo).execute()
    return [UserResponse(**vars(u)) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    repo: AbstractUserRepository = Depends(get_user_repository),
):
    user = await GetUser(repo).execute(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**vars(user))

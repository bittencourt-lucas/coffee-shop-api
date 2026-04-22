from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse

from src.core.exceptions import DuplicateEmailError
from src.core.repositories import AbstractIdempotencyRepository, AbstractUserRepository
from src.infrastructure.api.dependencies import get_current_user, get_idempotency_repository, get_user_repository
from src.infrastructure.api.schemas import UserCreate, UserResponse
from src.infrastructure.auth.jwt import TokenData
from src.use_cases.user import CreateUser, GetUser

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    user_repo: AbstractUserRepository = Depends(get_user_repository),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    idempotency_repo: AbstractIdempotencyRepository = Depends(get_idempotency_repository),
):
    if idempotency_key:
        if len(idempotency_key) > 128:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Idempotency-Key must be 128 characters or fewer",
            )
        cached = await idempotency_repo.get(idempotency_key)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.body)

    try:
        user = await CreateUser(user_repo).execute(
            email=body.email,
            password=body.password,
        )
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    response = UserResponse(id=user.id, email=user.email, role=user.role)

    if idempotency_key:
        await idempotency_repo.save(
            idempotency_key, status.HTTP_201_CREATED, response.model_dump(mode="json")
        )

    return response


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    repo: AbstractUserRepository = Depends(get_user_repository),
    _: TokenData = Depends(get_current_user),
):
    user = await GetUser(repo).execute(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=user.id, email=user.email, role=user.role)

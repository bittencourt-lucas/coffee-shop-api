from fastapi import APIRouter, Depends, HTTPException, status

from src.core.exceptions import InvalidCredentialsError
from src.core.repositories import AbstractUserRepository
from src.infrastructure.api.dependencies import get_user_repository
from src.infrastructure.api.schemas import SignInRequest, TokenResponse
from src.use_cases.user import SignIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(
    body: SignInRequest,
    user_repo: AbstractUserRepository = Depends(get_user_repository),
):
    try:
        token = await SignIn(user_repo).execute(email=body.email, password=body.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return TokenResponse(access_token=token)

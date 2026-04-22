from fastapi import APIRouter, Depends, HTTPException, status

from src.core.exceptions import InvalidCredentialsError
from src.core.repositories import AbstractRevokedTokenRepository, AbstractUserRepository
from src.infrastructure.api.dependencies import get_current_user, get_revoked_token_repository, get_user_repository
from src.infrastructure.api.schemas import SignInRequest, TokenResponse
from src.infrastructure.auth.jwt import TokenData
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


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    current_user: TokenData = Depends(get_current_user),
    revoked_repo: AbstractRevokedTokenRepository = Depends(get_revoked_token_repository),
):
    await revoked_repo.revoke(current_user.jti, current_user.expires_at)

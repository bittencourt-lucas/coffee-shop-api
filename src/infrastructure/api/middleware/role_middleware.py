import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.enums import Role
from src.infrastructure.settings import settings

logger = logging.getLogger(__name__)


class RoleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            request.state.role = Role.CUSTOMER
            return await call_next(request)

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header must use Bearer scheme."},
            )

        token = auth_header[len("Bearer "):]
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            request.state.role = Role(payload["role"])
        except (JWTError, KeyError, ValueError):
            logger.debug("Invalid or expired token received")
            return JSONResponse(status_code=401, content={"detail": "Invalid or expired token."})

        return await call_next(request)

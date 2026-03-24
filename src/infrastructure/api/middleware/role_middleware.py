from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.enums import Role

ROLE_HEADER = "X-Role"


class RoleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        raw = request.headers.get(ROLE_HEADER, Role.CUSTOMER.value)
        try:
            request.state.role = Role(raw)
        except ValueError:
            valid = ", ".join(r.value for r in Role)
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid role '{raw}'. Valid values: {valid}."},
            )
        return await call_next(request)

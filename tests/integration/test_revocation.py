from uuid import uuid4

import pytest

from src.core.enums import Role
from src.infrastructure.api.dependencies import (
    get_order_repository,
    get_product_repository,
    get_revoked_token_repository,
    get_user_repository,
)
from src.infrastructure.auth.jwt import create_access_token
from src.infrastructure.database.repositories import (
    OrderRepository,
    ProductRepository,
    RevokedTokenRepository,
    UserRepository,
)
from src.main import app

from tests.integration.conftest import _ClientContext


@pytest.fixture
async def revocation_client(test_db):
    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)
    app.dependency_overrides[get_revoked_token_repository] = lambda: RevokedTokenRepository(test_db)
    app.dependency_overrides[get_order_repository] = lambda: OrderRepository(test_db)
    app.dependency_overrides[get_product_repository] = lambda: ProductRepository(test_db)

    async with _ClientContext(test_db) as c:
        await c.post("/users/", json={"email": "rev@example.com", "password": "secret123", "role": "CUSTOMER"})
        yield c


def _make_token(role: Role = Role.CUSTOMER) -> str:
    return create_access_token(user_id=uuid4(), role=role)


class TestSignOut:
    async def test_sign_out_returns_204(self, revocation_client):
        token = _make_token()
        response = await revocation_client.post(
            "/auth/sign-out", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 204

    async def test_revoked_token_is_rejected_on_subsequent_request(self, revocation_client):
        token = _make_token()
        await revocation_client.post("/auth/sign-out", headers={"Authorization": f"Bearer {token}"})
        response = await revocation_client.get(
            f"/users/{uuid4()}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_sign_out_is_idempotent(self, revocation_client):
        token = _make_token()
        await revocation_client.post("/auth/sign-out", headers={"Authorization": f"Bearer {token}"})
        response = await revocation_client.post(
            "/auth/sign-out", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_sign_out_without_token_returns_401(self, revocation_client):
        response = await revocation_client.post("/auth/sign-out")
        assert response.status_code == 401

    async def test_different_tokens_are_independent(self, revocation_client):
        token_a = _make_token()
        token_b = _make_token()
        await revocation_client.post("/auth/sign-out", headers={"Authorization": f"Bearer {token_a}"})
        response = await revocation_client.get(
            f"/users/{uuid4()}", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert response.status_code == 404

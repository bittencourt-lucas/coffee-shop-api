import pytest

from src.infrastructure.api.dependencies import get_user_repository
from src.infrastructure.database.repositories import UserRepository
from src.main import app
from tests.integration.conftest import _ClientContext

_USER_PAYLOAD = {"email": "bob@example.com", "password": "hunter22"}


@pytest.fixture
async def auth_client(test_db):
    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)

    async with _ClientContext(test_db) as c:
        await c.post("/users/", json=_USER_PAYLOAD)
        yield c


class TestSignInStatus:
    async def test_returns_200_for_valid_credentials(self, auth_client):
        response = await auth_client.post(
            "/auth/sign-in", json={"email": _USER_PAYLOAD["email"], "password": _USER_PAYLOAD["password"]}
        )
        assert response.status_code == 200

    async def test_returns_401_for_wrong_password(self, auth_client):
        response = await auth_client.post(
            "/auth/sign-in", json={"email": _USER_PAYLOAD["email"], "password": "wrong"}
        )
        assert response.status_code == 401

    async def test_returns_401_for_unknown_email(self, auth_client):
        response = await auth_client.post(
            "/auth/sign-in", json={"email": "nobody@example.com", "password": "any"}
        )
        assert response.status_code == 401

    async def test_returns_422_on_missing_fields(self, auth_client):
        response = await auth_client.post("/auth/sign-in", json={"email": "bob@example.com"})
        assert response.status_code == 422


class TestSignInResponse:
    async def test_response_contains_access_token(self, auth_client):
        data = (await auth_client.post(
            "/auth/sign-in", json={"email": _USER_PAYLOAD["email"], "password": _USER_PAYLOAD["password"]}
        )).json()
        assert "access_token" in data

    async def test_response_token_type_is_bearer(self, auth_client):
        data = (await auth_client.post(
            "/auth/sign-in", json={"email": _USER_PAYLOAD["email"], "password": _USER_PAYLOAD["password"]}
        )).json()
        assert data["token_type"] == "bearer"

    async def test_access_token_is_a_non_empty_string(self, auth_client):
        data = (await auth_client.post(
            "/auth/sign-in", json={"email": _USER_PAYLOAD["email"], "password": _USER_PAYLOAD["password"]}
        )).json()
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 0

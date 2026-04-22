from uuid import uuid4

import pytest

from src.core.enums import Role
from src.infrastructure.api.dependencies import get_idempotency_repository, get_user_repository
from src.infrastructure.auth.jwt import create_access_token
from src.infrastructure.database.repositories import IdempotencyRepository, UserRepository
from src.main import app
from tests.integration.conftest import _ClientContext


@pytest.fixture
async def user_client(test_db):
    app.dependency_overrides[get_user_repository] = lambda: UserRepository(test_db)
    app.dependency_overrides[get_idempotency_repository] = lambda: IdempotencyRepository(test_db)

    async with _ClientContext(test_db) as c:
        yield c


def _auth_headers() -> dict:
    token = create_access_token(user_id=uuid4(), role=Role.CUSTOMER)
    return {"Authorization": f"Bearer {token}"}


_USER_PAYLOAD = {"email": "alice@example.com", "password": "secure123"}


class TestCreateUserStatus:
    async def test_returns_201_on_success(self, user_client):
        response = await user_client.post("/users/", json=_USER_PAYLOAD)
        assert response.status_code == 201

    async def test_returns_409_on_duplicate_email(self, user_client):
        await user_client.post("/users/", json=_USER_PAYLOAD)
        response = await user_client.post("/users/", json=_USER_PAYLOAD)
        assert response.status_code == 409

    async def test_returns_422_on_missing_fields(self, user_client):
        response = await user_client.post("/users/", json={"email": "a@b.com"})
        assert response.status_code == 422

    async def test_returns_422_on_short_password(self, user_client):
        response = await user_client.post("/users/", json={"email": "a@b.com", "password": "short"})
        assert response.status_code == 422

    async def test_role_field_is_ignored_and_always_customer(self, user_client):
        payload = {**_USER_PAYLOAD, "role": "MANAGER"}
        data = (await user_client.post("/users/", json=payload)).json()
        assert data["role"] == "CUSTOMER"


class TestCreateUserResponse:
    async def test_response_contains_id(self, user_client):
        data = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()
        assert "id" in data

    async def test_response_email_matches_request(self, user_client):
        data = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()
        assert data["email"] == _USER_PAYLOAD["email"]

    async def test_response_role_is_always_customer(self, user_client):
        data = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()
        assert data["role"] == "CUSTOMER"

    async def test_response_does_not_expose_password_hash(self, user_client):
        data = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()
        assert "password_hash" not in data
        assert "password" not in data


class TestGetUser:
    async def test_returns_200_for_existing_user(self, user_client):
        user_id = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()["id"]
        response = await user_client.get(f"/users/{user_id}", headers=_auth_headers())
        assert response.status_code == 200

    async def test_returns_correct_user(self, user_client):
        user_id = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()["id"]
        data = (await user_client.get(f"/users/{user_id}", headers=_auth_headers())).json()
        assert data["id"] == user_id
        assert data["email"] == _USER_PAYLOAD["email"]

    async def test_returns_404_for_unknown_id(self, user_client):
        response = await user_client.get(f"/users/{uuid4()}", headers=_auth_headers())
        assert response.status_code == 404

    async def test_returns_401_without_token(self, user_client):
        user_id = (await user_client.post("/users/", json=_USER_PAYLOAD)).json()["id"]
        response = await user_client.get(f"/users/{user_id}")
        assert response.status_code == 401


class TestCreateUserIdempotency:
    async def test_duplicate_key_returns_201(self, user_client):
        key = str(uuid4())
        await user_client.post("/users/", json=_USER_PAYLOAD, headers={"Idempotency-Key": key})
        response = await user_client.post(
            "/users/", json={"email": "other@example.com", "password": "password1"},
            headers={"Idempotency-Key": key},
        )
        assert response.status_code == 201

    async def test_duplicate_key_returns_same_user_id(self, user_client):
        key = str(uuid4())
        headers = {"Idempotency-Key": key}
        first = (await user_client.post("/users/", json=_USER_PAYLOAD, headers=headers)).json()
        second = (await user_client.post("/users/", json=_USER_PAYLOAD, headers=headers)).json()
        assert first["id"] == second["id"]

    async def test_different_keys_allow_different_users(self, user_client):
        first = (await user_client.post(
            "/users/",
            json={"email": "a@example.com", "password": "password1"},
            headers={"Idempotency-Key": str(uuid4())},
        )).json()
        second = (await user_client.post(
            "/users/",
            json={"email": "b@example.com", "password": "password2"},
            headers={"Idempotency-Key": str(uuid4())},
        )).json()
        assert first["id"] != second["id"]

    async def test_returns_400_on_key_exceeding_128_characters(self, user_client):
        long_key = "x" * 129
        response = await user_client.post("/users/", json=_USER_PAYLOAD, headers={"Idempotency-Key": long_key})
        assert response.status_code == 400

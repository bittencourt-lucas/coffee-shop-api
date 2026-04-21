from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.entities import User
from src.core.enums import Role
from src.use_cases.user import CreateUser, GetUser


def _make_user(role: Role = Role.CUSTOMER) -> User:
    return User(id=uuid4(), email="user@example.com", role=role)


@pytest.fixture
def user_repo() -> AsyncMock:
    mock = AsyncMock()
    mock.create.side_effect = lambda user: user
    return mock


# --- CreateUser ---

async def test_create_user_returns_user_with_provided_email_and_role(user_repo):
    user = await CreateUser(user_repo).execute(email="a@b.com", role=Role.CUSTOMER)

    assert user.email == "a@b.com"
    assert user.role == Role.CUSTOMER


async def test_create_user_assigns_a_uuid(user_repo):
    user = await CreateUser(user_repo).execute(email="a@b.com", role=Role.CUSTOMER)

    assert user.id is not None


async def test_create_user_calls_repository(user_repo):
    await CreateUser(user_repo).execute(email="a@b.com", role=Role.MANAGER)

    user_repo.create.assert_called_once()


async def test_create_user_passes_correct_entity_to_repository(user_repo):
    await CreateUser(user_repo).execute(email="mgr@shop.com", role=Role.MANAGER)

    created: User = user_repo.create.call_args[0][0]
    assert created.email == "mgr@shop.com"
    assert created.role == Role.MANAGER


# --- GetUser ---

async def test_get_user_returns_user_when_found(user_repo):
    expected = _make_user()
    user_repo.get_by_id.return_value = expected

    result = await GetUser(user_repo).execute(expected.id)

    assert result == expected


async def test_get_user_returns_none_when_not_found(user_repo):
    user_repo.get_by_id.return_value = None

    result = await GetUser(user_repo).execute(uuid4())

    assert result is None


async def test_get_user_calls_repository_with_correct_id(user_repo):
    user_id = uuid4()
    user_repo.get_by_id.return_value = None

    await GetUser(user_repo).execute(user_id)

    user_repo.get_by_id.assert_called_once_with(user_id)

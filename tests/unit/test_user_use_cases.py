from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.core.entities import User
from src.core.enums import Role
from src.core.exceptions import InvalidCredentialsError
from src.use_cases.user import CreateUser, GetUser, SignIn


def _make_user(role: Role = Role.CUSTOMER, password_hash: str = "$2b$12$fakehash") -> User:
    return User(id=uuid4(), email="user@example.com", role=role, password_hash=password_hash)


@pytest.fixture
def user_repo() -> AsyncMock:
    mock = AsyncMock()
    mock.create.side_effect = lambda user: user
    return mock


# --- CreateUser ---

async def test_create_user_returns_user_with_provided_email(user_repo):
    user = await CreateUser(user_repo).execute(email="a@b.com", password="secret123")

    assert user.email == "a@b.com"


async def test_create_user_always_assigns_customer_role(user_repo):
    user = await CreateUser(user_repo).execute(email="a@b.com", password="secret123")

    assert user.role == Role.CUSTOMER


async def test_create_user_assigns_a_uuid(user_repo):
    user = await CreateUser(user_repo).execute(email="a@b.com", password="secret123")

    assert user.id is not None


async def test_create_user_calls_repository(user_repo):
    await CreateUser(user_repo).execute(email="a@b.com", password="secret123")

    user_repo.create.assert_called_once()


async def test_create_user_passes_correct_entity_to_repository(user_repo):
    await CreateUser(user_repo).execute(email="mgr@shop.com", password="secret123")

    created: User = user_repo.create.call_args[0][0]
    assert created.email == "mgr@shop.com"
    assert created.role == Role.CUSTOMER


async def test_create_user_hashes_password(user_repo):
    await CreateUser(user_repo).execute(email="a@b.com", password="mypassword")

    created: User = user_repo.create.call_args[0][0]
    assert created.password_hash != "mypassword"
    assert created.password_hash.startswith("$2b$")


async def test_create_user_does_not_store_plaintext_password(user_repo):
    await CreateUser(user_repo).execute(email="a@b.com", password="secret123")

    created: User = user_repo.create.call_args[0][0]
    assert "secret123" not in created.password_hash


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


# --- SignIn ---

async def test_sign_in_returns_token_for_valid_credentials(user_repo):
    user = _make_user()
    user_repo.get_by_email.return_value = user

    with patch("src.use_cases.user.sign_in.verify_password", return_value=True), \
         patch("src.use_cases.user.sign_in.create_access_token", return_value="tok.en.here") as mock_token:
        result = await SignIn(user_repo).execute(email="user@example.com", password="correct")

    assert result == "tok.en.here"
    mock_token.assert_called_once_with(user.id, user.role)


async def test_sign_in_raises_for_wrong_password(user_repo):
    user = _make_user()
    user_repo.get_by_email.return_value = user

    with patch("src.use_cases.user.sign_in.verify_password", return_value=False):
        with pytest.raises(InvalidCredentialsError):
            await SignIn(user_repo).execute(email="user@example.com", password="wrong")


async def test_sign_in_raises_for_unknown_email(user_repo):
    user_repo.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await SignIn(user_repo).execute(email="nobody@example.com", password="any")


async def test_sign_in_calls_verify_password_even_when_email_not_found(user_repo):
    user_repo.get_by_email.return_value = None

    with patch("src.use_cases.user.sign_in.verify_password", return_value=False) as mock_verify:
        with pytest.raises(InvalidCredentialsError):
            await SignIn(user_repo).execute(email="nobody@example.com", password="any")

    mock_verify.assert_called_once()


async def test_sign_in_calls_repository_with_provided_email(user_repo):
    user_repo.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await SignIn(user_repo).execute(email="check@example.com", password="any")

    user_repo.get_by_email.assert_called_once_with("check@example.com")

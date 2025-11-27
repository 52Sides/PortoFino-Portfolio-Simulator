import pytest
from typing import cast
from pydantic import EmailStr

from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from core.auth.auth_service import AuthService
from schemas.auth import RegisterSchema, LoginSchema, TokenResponse


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_user_success(monkeypatch):
    """Successful user registration."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar = MagicMock(return_value=None)
    mock_db.add = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    monkeypatch.setattr("core.auth.auth_service.hash_password", lambda p: f"hashed-{p}")

    email: EmailStr = cast(EmailStr, "user@test.com")
    data = RegisterSchema(email=email, password="pass123")
    result = await AuthService.register_user(data, mock_db)

    assert result["email"] == data.email
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited()
    mock_db.refresh.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_user_duplicate(monkeypatch):
    """Duplicate user registration must raise 400."""
    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar = AsyncMock(return_value=MagicMock())

    email: EmailStr = cast(EmailStr, "user@test.com")
    data = RegisterSchema(email=email, password="pass123")

    with pytest.raises(HTTPException) as exc:
        await AuthService.register_user(data, mock_db)

    assert exc.value.status_code == 400
    assert "exists" in exc.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_user_success(monkeypatch):
    """Valid login returns tokens."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.hashed_password = "hashed-pass"

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    monkeypatch.setattr("core.auth.auth_service.verify_password", lambda pw, hpw: True)
    monkeypatch.setattr("core.auth.auth_service.create_access_token", lambda uid: f"access-{uid}")
    monkeypatch.setattr("core.auth.auth_service.create_refresh_token", AsyncMock(return_value="refresh-1"))

    email: EmailStr = cast(EmailStr, "user@test.com")
    data = LoginSchema(email=email, password="pass123")
    result = await AuthService.login_user(data, mock_db)

    assert isinstance(result, TokenResponse)
    assert result.access_token.startswith("access-")
    assert result.refresh_token == "refresh-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_user_invalid_credentials(monkeypatch):
    """Invalid login credentials raise 401."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.hashed_password = "hashed-pass"

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    monkeypatch.setattr("core.auth.auth_service.verify_password", lambda pw, hpw: False)

    email: EmailStr = cast(EmailStr, "user@test.com")
    data = LoginSchema(email=email, password="wrong")

    with pytest.raises(HTTPException) as exc:
        await AuthService.login_user(data, mock_db)

    assert exc.value.status_code == 401
    assert "invalid" in exc.value.detail.lower()

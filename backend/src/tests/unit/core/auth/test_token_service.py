import pytest
from datetime import datetime, timedelta, timezone

from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from core.auth.token_service import TokenService


@pytest.fixture
def mock_token():
    """Mock RefreshTokenModel with a valid TTL."""
    class Token:
        token = "refresh123"
        user_id = 1
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    return Token()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_access_token_success(mock_token):
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_token)

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("core.auth.token_service.create_access_token", return_value="new_access_token"):
        result = await TokenService.refresh_access_token("refresh123", mock_db)

    assert result == {"access_token": "new_access_token", "token_type": "bearer"}
    mock_db.execute.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_access_token_expired(mock_token):
    mock_token.expires_at = datetime.now(tz=timezone.utc) - timedelta(minutes=1)

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_token)

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await TokenService.refresh_access_token("refresh123", mock_db)

    assert exc.value.status_code == 401
    assert "Expired refresh token" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token():
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await TokenService.refresh_access_token("invalid", mock_db)

    assert exc.value.status_code == 401
    assert "Invalid refresh token" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_logout_success():
    mock_db = AsyncMock()

    result = await TokenService.logout("refresh123", mock_db)

    assert result == {"detail": "Logged out"}
    mock_db.execute.assert_awaited_once()
    mock_db.commit.assert_awaited_once()

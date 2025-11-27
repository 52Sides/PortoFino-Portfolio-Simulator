import pytest

from unittest.mock import AsyncMock

from core.auth.utils import hash_password, verify_password, create_refresh_token, create_access_token


@pytest.mark.unit
def test_hash_and_verify_password():
    password = "Test123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpass", hashed)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_tokens():
    mock_db = AsyncMock()
    user_id = 1

    access = create_access_token(user_id)
    refresh = await create_refresh_token(user_id, db=mock_db)

    assert access.startswith("ey")
    assert len(refresh) > 0
    mock_db.execute.assert_awaited()
    mock_db.commit.assert_awaited()

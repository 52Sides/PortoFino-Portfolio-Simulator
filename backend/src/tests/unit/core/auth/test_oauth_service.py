import pytest

from unittest.mock import AsyncMock
from fastapi import HTTPException

from core.auth.oauth_service import OAuthService
from db.models.user_model import UserModel


@pytest.mark.unit
@pytest.mark.asyncio
async def test_google_callback_new_user(async_test_db, monkeypatch):
    mock_oauth = AsyncMock()
    mock_oauth.authorize_access_token = AsyncMock(
        return_value={"access_token": "token123"}
    )

    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value={"email": "new@test.com"})
    mock_oauth.get = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr("core.auth.oauth_service.get_oauth_client", lambda: mock_oauth)

    db = async_test_db()
    redirect_response = await OAuthService.google_callback(request=None, db=db)

    from sqlalchemy import select
    q = await db.execute(select(UserModel).where(UserModel.email == "new@test.com"))
    user = q.scalar_one_or_none()
    assert user is not None
    assert redirect_response.status_code == 307


@pytest.mark.unit
@pytest.mark.asyncio
async def test_google_callback_existing_user(async_test_db, monkeypatch):
    db = async_test_db()
    user = UserModel(email="exist@test.com", hashed_password=None)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    mock_oauth = AsyncMock()
    mock_oauth.authorize_access_token = AsyncMock(
        return_value={"access_token": "token123"}
    )

    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value={"email": "exist@test.com"})
    mock_oauth.get = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr("core.auth.oauth_service.get_oauth_client", lambda: mock_oauth)

    redirect_response = await OAuthService.google_callback(request=None, db=db)
    assert redirect_response.status_code == 307


@pytest.mark.unit
@pytest.mark.asyncio
async def test_google_callback_no_userinfo(async_test_db, monkeypatch):
    mock_oauth = AsyncMock()
    mock_oauth.authorize_access_token = AsyncMock(return_value={"access_token": "token123"})

    mock_resp = AsyncMock()
    mock_resp.json = AsyncMock(return_value={})
    mock_oauth.get = AsyncMock(return_value=mock_resp)

    monkeypatch.setattr("core.auth.oauth_service.get_oauth_client", lambda: mock_oauth)

    db = async_test_db()
    with pytest.raises(HTTPException) as exc:
        await OAuthService.google_callback(request=None, db=db)

    assert exc.value.status_code == 400

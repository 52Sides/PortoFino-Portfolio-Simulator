import pytest
from datetime import datetime, timedelta, timezone

from core.auth.utils import hash_password
from db.models import UserModel
from db.models.refresh_token_model import RefreshTokenModel


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_success(async_client, db_session):
    await async_client.post("/auth/register", json={"email": "r1@test.com", "password": "pass123"})
    r = await async_client.post("/auth/login", data={"username": "r1@test.com", "password": "pass123"})
    refresh = r.json()["refresh_token"]

    r2 = await async_client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_invalid(async_client):
    r = await async_client.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid refresh token"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_expired(test_client, db_session):
    user = UserModel(email="r2@test.com", hashed_password=hash_password("pass123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expired_token = RefreshTokenModel(
        token="expiredtoken123",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(expired_token)
    await db_session.commit()

    r = await test_client.post("/auth/refresh", json={"refresh_token": expired_token.token})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid refresh token"

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_success(async_client):
    await async_client.post("/auth/register", json={"email": "login@test.com", "password": "pass123"})

    resp = await async_client.post("/auth/login", data={"username": "login@test.com", "password": "pass123"})
    assert resp.status_code == 200
    tokens = resp.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    refresh = tokens["refresh_token"]

    resp = await async_client.post("/auth/logout", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Logged out"

    resp = await async_client.post("/auth/login", data={"username": "login@test.com", "password": "bad"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_user_not_exists(test_client):
    resp = await test_client.post("/auth/login", data={"username": "n234fdsf@test.com", "password": "pass123"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"

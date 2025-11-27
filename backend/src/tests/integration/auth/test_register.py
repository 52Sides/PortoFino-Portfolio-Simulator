import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_success(test_client):
    r = await test_client.post("/auth/register", json={"email": "user1@test.com", "password": "pass123"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["email"] == "user1@test.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_duplicate(test_client):
    await test_client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    r = await test_client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    assert r.status_code == 400
    assert r.json()["detail"] == "User already exists"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_invalid_email(test_client):
    r = await test_client.post("/auth/register", json={"email": "bad", "password": "pass123"})
    assert r.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_short_password(test_client):
    r = await test_client.post("/auth/register", json={"email": "x@test.com", "password": "1"})
    assert r.status_code == 422

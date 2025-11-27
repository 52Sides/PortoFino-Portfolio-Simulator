import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_protected_endpoint_requires_token(test_client):
    resp = await test_client.post("/simulate/", json={"command": "TSLA-L-100% 2020-01-01 2020-12-31"})
    assert resp.status_code == 401

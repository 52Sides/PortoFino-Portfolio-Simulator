import asyncio
import json
import pytest

from websockets import connect as ws_connect

WS_URL = "ws://localhost:8000/ws/simulations"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_simulation_full_flow_e2e(async_client):
    email = "e2e_test@example.com"
    password = "password123"

    # --- Register/login ---
    register_resp = await async_client.post("/auth/register", json={"email": email, "password": password})
    assert register_resp.status_code in (201, 400)

    login_resp = await async_client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_resp.status_code == 200, login_resp.text
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # --- Simulation ---
    sim_resp = await async_client.post(
        "/simulate/",
        json={"command": "AAPL-L-100% 2020-01-01 2020-12-31"},
        headers=headers
    )
    assert sim_resp.status_code == 200, sim_resp.text
    task_id = sim_resp.json()["task_id"]

    # --- WebSocket ---
    ws_url = f"{WS_URL}/{task_id}?token={access_token}"
    async with ws_connect(ws_url) as ws:
        ws_event_raw = await asyncio.wait_for(ws.recv(), timeout=20)
        ws_event = json.loads(ws_event_raw)

    assert ws_event["status"] == "done"

    payload = ws_event["data"]
    assert "cagr" in payload
    assert "sharpe" in payload
    assert "max_drawdown" in payload
    assert "portfolio_value" in payload

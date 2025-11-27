import asyncio
import json
import pytest

from websockets import connect as ws_connect

WS_URL = "ws://localhost:8000/ws/reports"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_simulations_history_flow_with_report(async_client):
    email = "testuser@example.com"
    password = "pass123"

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
        json={"command": "TSLA-L-50% NVDA-L-50% 2020-01-01 2020-12-31"},
        headers=headers
    )
    print(sim_resp.json())
    sim_task_id = sim_resp.json()["task_id"]
    assert sim_task_id

    # --- History ---
    history_resp = await async_client.get("/history/", headers=headers)
    sim_history_id = history_resp.json()["root"][0]["id"]
    assert sim_history_id

    # --- Report ---
    report_resp = await async_client.post(
        "/report/",
        json={"simulation_id": sim_history_id},
        headers=headers
    )
    assert report_resp.status_code == 200
    report_task_id = report_resp.json()["task_id"]
    assert report_task_id

    # --- Websocket ---
    ws_url = f"{WS_URL}/{report_task_id}?token={access_token}"
    async with ws_connect(ws_url) as websocket:
        event_raw = await asyncio.wait_for(websocket.recv(), timeout=60)
        data = json.loads(event_raw)

        assert data["task_id"] == report_task_id
        assert data["status"] in {"waiting", "done"}

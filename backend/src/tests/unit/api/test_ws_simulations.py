import pytest
import json

from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState
from unittest.mock import AsyncMock, MagicMock

from api.routers.ws_simulations import websocket_simulation


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_streams_events(mock_redis, mock_pubsub, monkeypatch):
    """Send a single event to the user."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[{"user_id": 1, "data": "ok"}]
        )
    )

    fake_user = MagicMock(id=1)
    await websocket_simulation(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"user_id": 1, "data": "ok"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_streams_events_done(mock_redis, mock_pubsub, monkeypatch):
    """Send multiple events, one with status 'done'."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[
                {"user_id": 1, "data": "ok"},
                {"user_id": 1, "data": "done", "status": "done"},
            ]
        )
    )

    fake_user = MagicMock(id=1)
    await websocket_simulation(ws, "abc123", fake_user)
    ws.accept.assert_awaited_once()
    assert ws.send_text.await_count == 2
    ws.send_text.assert_any_await(json.dumps({"user_id": 1, "data": "ok"}))
    ws.send_text.assert_any_await(json.dumps({"user_id": 1, "data": "done", "status": "done"}))
    assert ws.close.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_multiple_users(mock_redis, mock_pubsub, monkeypatch):
    """Ensure events for different users are filtered."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[
                {"user_id": 999, "data": "ignore"},
                {"user_id": 1, "data": "ok"},
                {"user_id": 2, "data": "ignore2"},
            ]
        )
    )

    fake_user = MagicMock(id=1)
    await websocket_simulation(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"user_id": 1, "data": "ok"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_disconnect(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            error=WebSocketDisconnect()
        )
    )

    await websocket_simulation(ws, "task42", MagicMock(id=1))

    ws.accept.assert_awaited_once()
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_exception(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            error=RuntimeError("boom")
        )
    )

    await websocket_simulation(ws, "err123", MagicMock(id=2))

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"error": "boom"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_simulation_ws_cannot_close(mock_redis, mock_pubsub, monkeypatch):
    """Ensure ws.close is not called if the websocket is already disconnected."""
    ws = AsyncMock()
    ws.application_state = WebSocketState.DISCONNECTED
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_simulations.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[{"user_id": 1, "data": "ok"}]
        )
    )

    fake_user = MagicMock(id=1)
    await websocket_simulation(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once()
    ws.close.assert_not_awaited()

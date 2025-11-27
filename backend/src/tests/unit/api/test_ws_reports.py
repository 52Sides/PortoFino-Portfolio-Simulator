import pytest
import json

from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState

from api.routers.ws_reports import websocket_report


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_streams_events(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[{"user_id": 999, "data": "ignore"}, {"user_id": 1, "data": "ok"}]
        )
    )

    fake_user = MagicMock(id=1)

    await websocket_report(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"user_id": 1, "data": "ok"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_disconnect(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            error=WebSocketDisconnect()
        )
    )

    await websocket_report(ws, "task42", MagicMock(id=1))

    ws.accept.assert_awaited_once()
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_exception_error(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            error=RuntimeError("boom")
        )
    )

    await websocket_report(ws, "err123", MagicMock(id=2))

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"error": "boom"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_streams_events_done(mock_redis, mock_pubsub, monkeypatch):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub(
            "chan",
            events=[
                {"user_id": 1, "data": "ok"},
                {"user_id": 1, "data": "done", "status": "done"},
            ]
        )
    )

    fake_user = MagicMock(id=1)
    await websocket_report(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    assert ws.send_text.await_count == 2
    ws.send_text.assert_any_await(json.dumps({"user_id": 1, "data": "ok"}))
    ws.send_text.assert_any_await(json.dumps({"user_id": 1, "data": "done", "status": "done"}))
    assert ws.close.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_cached_done(mock_redis, mock_pubsub, monkeypatch):
    """Check early exit when cached data contains an event with status=='done'."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = [json.dumps({"user_id": 1, "status": "done"})]

    fake_user = MagicMock(id=1)
    await websocket_report(ws, "task_done", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once_with(json.dumps({"user_id": 1, "status": "done"}))
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_ws_cannot_close(mock_redis, mock_pubsub, monkeypatch):
    """Ensure close is not called when the WebSocket is already DISCONNECTED."""
    ws = AsyncMock()
    ws.application_state = WebSocketState.DISCONNECTED
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub("chan", events=[{"user_id": 1, "data": "ok"}])
    )

    fake_user = MagicMock(id=1)
    await websocket_report(ws, "abc123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited_once()
    ws.close.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_empty_stream(mock_redis, mock_pubsub, monkeypatch):
    """Close the WebSocket when both cache and stream are empty."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    class EmptyPubSub:
        async def subscribe(self):
            if False:
                yield

        async def close(self):
            pass

    monkeypatch.setattr("api.routers.ws_reports.get_pubsub", lambda *a, **kw: EmptyPubSub())

    fake_user = MagicMock(id=1)
    await websocket_report(ws, "empty123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_not_awaited()
    ws.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_report_exception(mock_redis, mock_pubsub, monkeypatch):
    """Verify handling of RuntimeError during send."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock(side_effect=RuntimeError("send fail"))
    ws.close = AsyncMock()

    mock_redis.lrange_list.return_value = []

    monkeypatch.setattr(
        "api.routers.ws_reports.get_pubsub",
        lambda *a, **kw: mock_pubsub("chan", events=[{"user_id": 1, "data": "ok"}])
    )

    fake_user = MagicMock(id=1)
    await websocket_report(ws, "err123", fake_user)

    ws.accept.assert_awaited_once()
    ws.send_text.assert_awaited()
    ws.close.assert_awaited_once()

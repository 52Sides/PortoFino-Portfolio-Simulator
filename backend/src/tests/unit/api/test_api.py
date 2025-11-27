import pytest
import asyncio

from unittest.mock import AsyncMock, patch
from fastapi import FastAPI

from api.main import lifespan


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    async_connect = AsyncMock()
    async_close = AsyncMock()
    async_create_topics = AsyncMock()
    async_producer_start = AsyncMock()
    async_producer_stop = AsyncMock()

    async def fake_consume():
        await asyncio.sleep(0.01)

    class FakeTask:
        def __init__(self, coro):
            self._coro = coro
            self.cancel_called = False

        def cancel(self):
            self.cancel_called = True

        def __await__(self):
            return self._coro.__await__()

    fake_task = FakeTask(fake_consume())

    with patch("api.main.redis_client.connect", async_connect), \
         patch("api.main.redis_client.close", async_close), \
         patch("api.main.create_topics", async_create_topics), \
         patch("api.main.producer.start", async_producer_start), \
         patch("api.main.producer.stop", async_producer_stop), \
         patch("api.main.consume_events", fake_consume), \
         patch("api.main.asyncio.create_task", return_value=fake_task):

        app = FastAPI(lifespan=lifespan)

        async with lifespan(app):
            async_connect.assert_awaited_once()
            async_create_topics.assert_awaited_once()
            async_producer_start.assert_awaited_once()

        assert fake_task.cancel_called
        async_producer_stop.assert_awaited_once()
        async_close.assert_awaited_once()

import pytest
import asyncio
import json

import redis.asyncio as redis

from services.redis.pubsub import AsyncRedisPubSub, get_pubsub
from core.config import settings


@pytest.fixture(scope="function", autouse=True)
async def reset_shared_pool():
    """Reset the shared pool before each test."""
    AsyncRedisPubSub._shared_client = None
    yield
    AsyncRedisPubSub._shared_client = None


@pytest.fixture
async def redis_client():
    """Provide a Redis client for publish/subscribe tests."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_init_shared_creates_pool():
    assert AsyncRedisPubSub._shared_client is None
    await AsyncRedisPubSub.init_shared()
    assert isinstance(AsyncRedisPubSub._shared_client, redis.Redis)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_init_shared_idempotent():
    await AsyncRedisPubSub.init_shared()
    client1 = AsyncRedisPubSub._shared_client
    await AsyncRedisPubSub.init_shared()
    client2 = AsyncRedisPubSub._shared_client
    assert client1 is client2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_and_subscribe_receives_json(redis_client):
    pub = AsyncRedisPubSub("chan:test")
    await AsyncRedisPubSub.init_shared()

    messages = []

    async def reader():
        async for msg in pub.subscribe():
            messages.append(msg)
            if len(messages) >= 2:
                break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.1)

    await pub.publish({"msg": 1})
    await pub.publish({"msg": 2})

    await asyncio.wait_for(task, timeout=2)

    assert messages == [{"msg": 1}, {"msg": 2}]
    await pub.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscribe_invalid_json(redis_client):
    pub = AsyncRedisPubSub("chan:err")
    await AsyncRedisPubSub.init_shared()

    messages = []

    async def reader():
        async for msg in pub.subscribe():
            messages.append(msg)
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.1)
    await redis_client.publish("chan:err", "/// not json ///")

    await asyncio.wait_for(task, timeout=2)
    assert messages == [{"raw": "/// not json ///"}]
    await pub.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_unsub_and_cleanup(redis_client):
    pub = AsyncRedisPubSub("chan:close")
    await AsyncRedisPubSub.init_shared()

    async def reader():
        async for msg in pub.subscribe():
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.1)
    await pub.close()
    assert pub._pubsub is None

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_pubsub_returns_correct_channel():
    p = get_pubsub("prefix", "123")
    assert isinstance(p, AsyncRedisPubSub)
    assert p.channel == "prefix:123"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscribe_ignores_non_message_types(redis_client):
    pub = AsyncRedisPubSub("chan:ignore")
    await AsyncRedisPubSub.init_shared()

    received = []

    async def reader():
        async for msg in pub.subscribe():
            received.append(msg)
            break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.1)
    await redis_client.publish(pub.channel, json.dumps({"ok": True}))

    await asyncio.wait_for(task, timeout=2)
    assert received == [{"ok": True}]
    await pub.close()

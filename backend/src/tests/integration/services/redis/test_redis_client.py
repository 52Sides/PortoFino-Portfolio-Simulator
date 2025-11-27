import pytest

from core.config import settings
from services.redis.client import RedisClient


@pytest.fixture(scope="session")
async def redis_available():
    client = RedisClient(url=settings.REDIS_URL)
    try:
        await client.connect()
        await client.client.ping()
        await client.close()
        return True
    except Exception:
        pytest.skip(f"Redis is not available at {settings.REDIS_URL}")


@pytest.fixture
async def redis_client(redis_available):
    client = RedisClient(url=settings.REDIS_URL)
    await client.connect()
    await client.client.flushdb()
    yield client
    if client._client:
        await client.client.flushdb()
        await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connect_sets_client(redis_client):
    assert redis_client.client is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_close_resets_client(redis_client):
    await redis_client.close()
    assert redis_client._client is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ttl_policy(redis_client):
    assert redis_client._get_ttl("simulate:123") == 3600
    assert redis_client._get_ttl("report:abc") == 3600
    assert redis_client._get_ttl("history:x") == 3600
    assert redis_client._get_ttl("unknown:key") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_set_and_get(redis_client):
    await redis_client.set("simulate:test1", "val1")
    val = await redis_client.get("simulate:test1")
    assert val == "val1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_set_manual_ttl(redis_client):
    await redis_client.set("simulate:test2", "val2", ex=2)
    ttl = await redis_client.client.ttl("simulate:test2")
    assert 0 < ttl <= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hset_and_hgetall(redis_client):
    await redis_client.hset("report:1", {"a": "1", "b": "2"})
    data = await redis_client.hgetall("report:1")
    assert data == {"a": "1", "b": "2"}
    ttl = await redis_client.client.ttl("report:1")
    assert 0 < ttl <= 3600


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete(redis_client):
    await redis_client.set("simulate:del", "x")
    await redis_client.delete("simulate:del")
    val = await redis_client.get("simulate:del")
    assert val is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rpush_and_lrange(redis_client):
    await redis_client.rpush_list("simulate:list1", "v1")
    await redis_client.rpush_list("simulate:list1", "v2")
    values = await redis_client.lrange_list("simulate:list1", 0, -1)
    assert values == ["v1", "v2"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lock_acquire_and_release(redis_client):
    async with redis_client.lock("lock:test", timeout=2):
        val = await redis_client.get("lock:test")
        assert val


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lock_double_acquire(redis_client):
    l1 = redis_client.client.lock("lock:double", timeout=2)
    await l1.acquire()

    l2 = redis_client.client.lock("lock:double", timeout=1, blocking=False)
    acquired = await l2.acquire()
    if acquired:
        await l2.release()
        pytest.fail("Should not acquire second lock")

    await redis_client.unlock(l1)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unlock_ignores_errors(redis_client):
    fake_lock = redis_client.client.lock("lock:fake", timeout=1)
    # Should not raise
    await redis_client.unlock(fake_lock)

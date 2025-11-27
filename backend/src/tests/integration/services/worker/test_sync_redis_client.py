import pytest
import uuid

from redis import Redis

from services.worker.sync_clients.redis_client import RedisClientSync, redis_sync_client


def unique_key(prefix: str) -> str:
    return f"pytest_{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
def test_connect_and_client():
    client = RedisClientSync()
    client.connect()
    assert isinstance(client.client, Redis)
    client.close()
    with pytest.raises(RuntimeError):
        _ = client.client


@pytest.mark.integration
def test_basic_operations():
    client = RedisClientSync()
    client.connect()

    key = unique_key("key")
    hash_key = unique_key("hash")

    client.set(key, "value1")
    assert client.get(key) == "value1"

    client.hset(hash_key, {"f1": "v1", "f2": "v2"})
    assert client.hgetall(hash_key) == {"f1": "v1", "f2": "v2"}

    client.delete(key)
    client.delete(hash_key)
    assert client.get(key) is None
    assert client.hgetall(hash_key) == {}


@pytest.mark.integration
def test_list_operations():
    client = RedisClientSync()
    client.connect()

    list_key = unique_key("list")
    client.rpush_list(list_key, "a")
    client.rpush_list(list_key, "b")
    assert client.lrange_list(list_key, 0, -1) == ["a", "b"]

    client.delete(list_key)


@pytest.mark.integration
def test_lock_acquire_release():
    client = RedisClientSync()
    client.connect()

    lock_key = unique_key("lock")
    with client.lock(lock_key, timeout=1, blocking_timeout=1) as lock:
        assert lock.locked()
        assert client.client.get(lock_key) is not None

    assert client.client.get(lock_key) is None


@pytest.mark.integration
def test_lock_failure():
    client = RedisClientSync()
    client.connect()

    lock_key = unique_key("lockfail")
    lock1 = client.client.lock(lock_key, timeout=5)
    lock1.acquire(blocking=False)

    with pytest.raises(RuntimeError):
        with client.lock(lock_key, timeout=1, blocking_timeout=0.1):
            pass

    lock1.release()


@pytest.mark.integration
def test_ttl_policy_applied():
    client = RedisClientSync()
    client.connect()

    sim_key = "simulate:" + unique_key("task")
    buf_key = "buffer:" + unique_key("task")

    client.set(sim_key, "v")
    ttl = client.client.ttl(sim_key)
    assert 0 < ttl <= 3600

    client.rpush_list(buf_key, "v")
    ttl_list = client.client.ttl(buf_key)
    assert 0 < ttl_list <= 900

    client.delete(sim_key)
    client.delete(buf_key)


@pytest.mark.integration
def test_singleton_usage():
    redis_sync_client.connect()
    key = unique_key("singleton")
    redis_sync_client.set(key, "val")
    assert redis_sync_client.get(key) == "val"
    redis_sync_client.delete(key)

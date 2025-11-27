import asyncio
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from redis.asyncio.lock import Lock
from redis.exceptions import LockError

from core.config import settings


class RedisClient:
    """Lightweight async Redis wrapper with TTL and lock helpers."""

    def __init__(self, url: str = settings.REDIS_URL, decode_responses: bool = True):
        self.url = url
        self.decode_responses = decode_responses
        self._client: redis.Redis | None = None

        self.ttl_policy = {
            "simulate": 3600,
            "report": 3600,
            "history": 3600,
        }

    # --- Initialization ---
    async def connect(self):
        """Initialize the Redis connection."""
        if not self._client:
            self._client = redis.from_url(self.url, decode_responses=self.decode_responses)

    async def close(self):
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Return the active Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect().")
        return self._client

    def _get_ttl(self, key: str) -> int | None:
        """Determines the TTL based on the key prefix."""
        prefix = key.split(":")[0]
        return self.ttl_policy.get(prefix)

    # --- Basic operations ---
    async def set(self, key: str, value: Any, ex: int | None = None):
        """Set a value with optional TTL."""
        ttl = ex or self._get_ttl(key)
        await self.client.set(key, value, ex=ttl)

    async def hset(self, key: str, mapping: dict, ex: int | None = None):
        """Set hash fields and apply TTL."""
        await self.client.hset(key, mapping=mapping)
        ttl = ex or self._get_ttl(key)
        if ttl:
            await self.client.expire(key, ttl)

    async def get(self, key: str) -> Any:
        """Fetch a key value."""
        return await self.client.get(key)

    async def hgetall(self, key: str) -> dict:
        """Fetch all hash fields."""
        return await self.client.hgetall(key)

    async def delete(self, key: str):
        """Delete a key."""
        await self.client.delete(key)

    # --- List operations ---
    async def rpush_list(self, key: str, value: Any, ex: int | None = None):
        """Append a value to a list and set TTL."""
        await self.client.rpush(key, value)
        ttl = ex or self._get_ttl(key)
        if ttl:
            await self.client.expire(key, ttl)

    async def lrange_list(self, key: str, start: int, end: int):
        """Return a list slice."""
        return await self.client.lrange(key, start, end)

    # --- Lock API ---
    @asynccontextmanager
    async def lock(self, name: str, timeout: int = 180, retry_delay: float = 0.1, max_retries: int = 30):
        """Async distributed lock with retry support."""
        lock = self.client.lock(name, timeout=timeout)
        for attempt in range(max_retries):
            try:
                acquired = await lock.acquire()
                if acquired:
                    break
            except RuntimeError:

                lock = self.client.lock(name, timeout=timeout)
            await asyncio.sleep(retry_delay)
        else:
            raise RuntimeError(f"Could not acquire lock {name} after {max_retries} retries")

        try:
            yield lock
        finally:
            await self.unlock(lock)

    @staticmethod
    async def unlock(lock: Lock):
        """Release a Redis lock safely."""
        try:
            await lock.release()
        except (LockError, RuntimeError):
            pass


# --- FastAPI singleton ---
redis_client = RedisClient()

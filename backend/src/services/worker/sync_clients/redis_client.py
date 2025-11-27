from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import redis
from redis.lock import Lock
from redis.exceptions import LockError

from core.config import settings


class RedisClientSync:
    """Sync Redis wrapper for Celery workers."""

    def __init__(self, url: str = settings.REDIS_URL, decode_responses: bool = True):
        self.url = url
        self.decode_responses = decode_responses
        self._client: redis.Redis | None = None

        self.ttl_policy = {
            "simulate": 3600,
            "report": 3600,
            "history": 3600,
            "buffer": 900
        }

    def connect(self):
        if not self._client:
            self._client = redis.from_url(self.url, decode_responses=self.decode_responses)

    def close(self):
        if self._client:
            try:
                self._client.close()
            finally:
                self._client = None

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect().")
        return self._client

    def _get_ttl(self, key: str) -> int | None:
        prefix = key.split(":")[0]
        return self.ttl_policy.get(prefix)

    def set(self, key: str, value: Any, ex: int | None = None):
        ttl = ex or self._get_ttl(key)
        self.client.set(key, value, ex=ttl)

    def hset(self, key: str, mapping: dict, ex: int | None = None):
        self.client.hset(key, mapping=mapping)
        ttl = ex or self._get_ttl(key)
        if ttl:
            self.client.expire(key, ttl)

    def get(self, key: str) -> Any:
        return self.client.get(key)

    def hgetall(self, key: str) -> dict:
        return self.client.hgetall(key)

    def delete(self, key: str):
        self.client.delete(key)

    def rpush_list(self, key: str, value: Any, ex: int | None = None):
        """Append a value to a list and set TTL."""
        self.client.rpush(key, value)
        ttl = ex or self._get_ttl(key)
        if ttl:
            self.client.expire(key, ttl)

    def lrange_list(self, key: str, start: int, end: int):
        """Return a list slice."""
        return self.client.lrange(key, start, end)

    @contextmanager
    def lock(self, name: str, timeout: int = 180, blocking_timeout: int = 5):
        """Sync distributed lock with retry support."""
        lock = self.client.lock(
            name,
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )

        acquired = lock.acquire(blocking=True)
        if not acquired:
            raise RuntimeError(f"Could not acquire lock {name}")

        try:
            yield lock
        finally:
            self._safe_unlock(lock)

    @staticmethod
    def _safe_unlock(lock: Lock):
        """Release a Redis lock safely."""
        try:
            lock.release()
        except (LockError, RuntimeError):
            pass


# --- Singleton for Celery workers ---
redis_sync_client = RedisClientSync()

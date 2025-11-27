import json
import redis.asyncio as redis

from core.config import settings


class AsyncRedisPubSub:
    """Async wrapper for Redis Pub/Sub with a shared connection pool."""

    _shared_client: redis.Redis | None = None

    def __init__(self, channel: str):
        self.channel = channel
        self._pubsub = None

    @classmethod
    async def init_shared(cls):
        """Creates a single Redis client (pool) bound to the current loop."""
        if cls._shared_client is None:
            cls._shared_client = redis.from_url(settings.REDIS_URL, decode_responses=True, max_connections=5)

    async def publish(self, message: dict):
        await self.init_shared()
        await self._shared_client.publish(self.channel, json.dumps(message))

    async def subscribe(self):
        await self.init_shared()
        self._pubsub = self._shared_client.pubsub()
        await self._pubsub.subscribe(self.channel)

        async for msg in self._pubsub.listen():
            if msg["type"] == "message":
                try:
                    yield json.loads(msg["data"])
                except json.JSONDecodeError:
                    yield {"raw": msg["data"]}

    async def close(self):
        if self._pubsub:
            try:
                await self._pubsub.unsubscribe(self.channel)
                await self._pubsub.close()
            finally:
                self._pubsub = None


def get_pubsub(channel_prefix: str, task_id: str) -> AsyncRedisPubSub:
    """Get a Pub/Sub client for a task_id."""
    return AsyncRedisPubSub(f"{channel_prefix}:{task_id}")

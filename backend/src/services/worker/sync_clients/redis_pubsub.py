import json
import redis

from core.config import settings


class SyncRedisPubSub:
    """Synchronous Redis Pub/Sub with shared client."""

    _shared_client: redis.Redis | None = None

    def __init__(self, channel: str):
        self.channel = channel
        self._pubsub = None

    @classmethod
    def init_shared(cls):
        """Ensures a single sync Redis client exists."""
        if cls._shared_client is None:
            cls._shared_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=5
            )

    def publish(self, message: dict):
        """Publish JSON message to channel."""
        self.init_shared()
        payload = json.dumps(message)
        self._shared_client.publish(self.channel, payload)

    def subscribe(self):
        """Blocking generator. Yields parsed messages."""
        self.init_shared()
        self._pubsub = self._shared_client.pubsub()
        self._pubsub.subscribe(self.channel)

        for msg in self._pubsub.listen():
            if msg["type"] != "message":
                continue
            data = msg.get("data")
            if data is None:
                continue
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                yield {"raw": data}

    def close(self):
        """Unsubscribe and close pubsub."""
        if self._pubsub:
            try:
                self._pubsub.unsubscribe(self.channel)
                self._pubsub.close()
            finally:
                self._pubsub = None


def get_pubsub(channel_prefix: str, task_id: str) -> SyncRedisPubSub:
    """Returns sync Pub/Sub client for this task."""
    return SyncRedisPubSub(f"{channel_prefix}:{task_id}")

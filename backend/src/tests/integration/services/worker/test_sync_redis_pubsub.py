import json
import threading
import time
import uuid
import pytest

from services.worker.sync_clients.redis_pubsub import SyncRedisPubSub


def unique_channel(prefix="test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
def test_publish_and_subscribe_real():
    """Verify publish/subscribe without mocks, including JSON and invalid JSON."""
    channel = unique_channel()
    pubsub_client = SyncRedisPubSub(channel)

    received = []

    def subscriber():
        for msg in pubsub_client.subscribe():
            received.append(msg)
            if len(received) >= 3:
                break

    t = threading.Thread(target=subscriber)
    t.start()

    time.sleep(0.1)

    pubsub_client.publish({"a": 1})
    pubsub_client.publish({"b": 2})

    pubsub_client._shared_client.publish(channel, "not_json")

    t.join(timeout=2)

    assert {"a": 1} in received
    assert {"b": 2} in received
    assert {"raw": "not_json"} in received

    pubsub_client.close()
    assert pubsub_client._pubsub is None


@pytest.mark.integration
def test_close_without_subscribe():
    """Ensure closing without an active subscription does not error."""
    channel = unique_channel()
    pubsub_client = SyncRedisPubSub(channel)
    pubsub_client.close()
    assert pubsub_client._pubsub is None


@pytest.mark.integration
def test_multiple_clients_shared_connection():
    """Verify multiple clients share a single Redis connection and can publish/subscribe."""
    channel1 = unique_channel()
    channel2 = unique_channel()

    c1 = SyncRedisPubSub(channel1)
    c2 = SyncRedisPubSub(channel2)

    c1.init_shared()
    c2.init_shared()
    assert c1._shared_client is c2._shared_client

    t_msgs = []
    ready_event = threading.Event()

    def sub_thread():
        sub = SyncRedisPubSub(channel1)
        sub.init_shared()
        sub._pubsub = sub._shared_client.pubsub()
        sub._pubsub.subscribe(sub.channel)
        ready_event.set()

        for msg in sub._pubsub.listen():
            if msg["type"] != "message":
                continue
            data = msg.get("data")
            if data is None:
                continue
            try:
                t_msgs.append(json.loads(data))
            except json.JSONDecodeError:
                t_msgs.append({"raw": data})
            break
        sub.close()

    t = threading.Thread(target=sub_thread)
    t.start()

    ready_event.wait(timeout=1)
    assert ready_event.is_set(), "Subscription did not become ready"

    c1.publish({"x": 123})

    t.join(timeout=2)
    assert t_msgs, "No messages received from Redis"
    assert t_msgs[0] == {"x": 123}

    c1.close()
    c2.close()

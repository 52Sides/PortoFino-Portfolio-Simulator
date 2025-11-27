import json
import pytest
import pandas as pd
from contextlib import contextmanager

from unittest.mock import MagicMock, patch

from services.worker.tasks.simulation import run_simulation
from services.worker.sync_clients.redis_client import redis_sync_client
from services.worker.sync_clients.redis_pubsub import SyncRedisPubSub


def unique_key(prefix: str) -> str:
    import uuid
    return f"pytest_{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.mark.integration
def test_simulation_run_success(db_session):
    """run_simulation without a real DB, with real Redis and mocked pubsub/kafka"""

    db_session.execute(
        "INSERT INTO users (id, username) VALUES (:id, :username)",
        {"id": 42, "username": "pytest_user"}
    )
    db_session.commit()

    task_id = unique_key("task")
    redis_key = f"simulation:{task_id}"
    buf_key = f"buffer:simulation:{task_id}"
    redis_sync_client.connect()

    parsed_command = {
        "tickers": ["AAPL", "TSLA"],
        "weights": [0.5, 0.5],
        "sides": ["L", "S"],
        "start_date": "2020-01-01",
        "end_date": "2021-01-01",
    }

    combined_df = pd.DataFrame([
        {"ticker": "AAPL", "close": 100, "date": "2020-01-01"},
        {"ticker": "TSLA", "close": 200, "date": "2020-01-01"},
    ])

    cached = {
        "command": "AAPL-L-50% TSLA-S-50% 2020-01-01 2021-01-01",
        "user_id": 42,
        "parsed_command": json.dumps(parsed_command),
        "combined_df": combined_df.to_json(orient="records"),
    }

    redis_sync_client.client.hset(redis_key, mapping=cached)

    mock_pub = MagicMock(spec=SyncRedisPubSub)
    mock_pub.publish = MagicMock()

    @contextmanager
    def fake_db():
        db = MagicMock()
        yield db

    with patch("services.worker.tasks.simulation.get_pubsub", return_value=mock_pub), \
         patch("services.worker.tasks.simulation.producer_sync.publish_simulation_event") as mock_kafka, \
         patch("services.worker.tasks.simulation.get_sync_db", fake_db):

        run_simulation(task_id)

        # Redis buffer
        buf_items = redis_sync_client.lrange_list(buf_key, 0, -1)
        assert len(buf_items) == 1
        buf_data = json.loads(buf_items[0])
        assert buf_data["task_id"] == task_id
        assert buf_data["status"] == "done"

        # PubSub
        mock_pub.publish.assert_called_once()
        pub_data = mock_pub.publish.call_args[0][0]
        assert pub_data["task_id"] == task_id
        assert pub_data["user_id"] == 42
        assert pub_data["status"] == "done"

        # Kafka
        mock_kafka.assert_called_once()
        args = mock_kafka.call_args.kwargs
        assert args["task_id"] == task_id
        assert args["stage"] == "run_simulation"
        assert args["status"] == "done"

    # Redis key should delete
    assert redis_sync_client.client.exists(redis_key) == 0
    assert redis_sync_client.client.exists(buf_key) == 1

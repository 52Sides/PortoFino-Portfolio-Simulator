import json
import pytest

from unittest.mock import patch, MagicMock

from services.worker.tasks.report import run_report
from services.worker.sync_clients.redis_client import redis_sync_client


@pytest.mark.integration
def test_report_run_success(tmp_path):
    task_id = "55"
    key = f"report:{task_id}"
    buf_key = f"buffer:report:{task_id}"

    redis_sync_client.connect()

    fetched = {
        "simulation_id": 10,
        "user_id": 5,
        "a": 1,
    }

    redis_sync_client.hset(key, {
        "fetched_data": json.dumps(fetched)
    })

    file_path = tmp_path / "generated.xls"
    file_path.write_text("OK")

    mock_pub = MagicMock()
    mock_pub.publish = MagicMock()

    with patch("services.worker.tasks.report.generate_xls_report", return_value=str(file_path)), \
         patch("services.worker.tasks.report.get_pubsub", return_value=mock_pub), \
         patch("services.worker.tasks.report.producer_sync.publish_simulation_event") as mock_kafka:

        run_report(task_id)

        # pubsub
        mock_pub.publish.assert_called_once()
        pub_msg = mock_pub.publish.call_args[0][0]
        assert pub_msg["status"] == "done"
        assert pub_msg["download_url"].endswith("report_10.xls")

        # buffer in redis
        buf_items = redis_sync_client.lrange_list(buf_key, 0, -1)
        assert len(buf_items) == 1

        # Kafka event
        mock_kafka.assert_called_once()
        args = mock_kafka.call_args.kwargs
        assert args["task_id"] == task_id
        assert args["stage"] == "run_report"
        assert args["status"] == "done"

    redis_sync_client.delete(key)
    redis_sync_client.delete(buf_key)


@pytest.mark.integration
def test_report_run_missing_redis():
    task_id = "999"
    key = f"report:{task_id}"

    redis_sync_client.connect()
    redis_sync_client.delete(key)

    # should not raise
    run_report(task_id)


@pytest.mark.integration
def test_report_run_file_missing(tmp_path):
    task_id = "88"
    key = f"report:{task_id}"
    buf_key = f"buffer:report:{task_id}"

    redis_sync_client.connect()

    fetched = {
        "simulation_id": 123,
        "user_id": 9
    }

    redis_sync_client.hset(key, {
        "fetched_data": json.dumps(fetched)
    })

    missing_file = tmp_path / "nope.xls"

    mock_pub = MagicMock()
    mock_pub.publish = MagicMock()

    with patch("services.worker.tasks.report.generate_xls_report", return_value=str(missing_file)), \
         patch("services.worker.tasks.report.get_pubsub", return_value=mock_pub), \
         patch("services.worker.tasks.report.producer_sync.publish_simulation_event"):

        run_report(task_id)

        mock_pub.publish.assert_called_once()
        msg = mock_pub.publish.call_args[0][0]

        assert msg["status"] == "failed"
        assert msg["download_url"] is None

        buf_items = redis_sync_client.lrange_list(buf_key, 0, -1)
        assert len(buf_items) == 1

    redis_sync_client.delete(key)
    redis_sync_client.delete(buf_key)

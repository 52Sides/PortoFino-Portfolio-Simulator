import pytest

from celery import Celery

from core.config import settings
from services.worker.sync_clients.redis_client import redis_sync_client


@pytest.mark.integration
def test_celery_app_instance_import():
    from services.worker.celery_app import celery_app

    assert isinstance(celery_app, Celery)
    assert celery_app.main == "portofino"
    assert celery_app.conf.broker_url == settings.REDIS_URL
    assert celery_app.conf.result_backend == settings.REDIS_URL


@pytest.mark.integration
def test_beat_schedule_structure():
    from services.worker.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule

    assert "vacuum-every-night" in schedule
    assert "cluster-monthly" in schedule
    assert "cleanup-old-reports-daily" in schedule

    assert schedule["vacuum-every-night"]["task"] == "vacuum_analyze_task"
    assert schedule["cluster-monthly"]["task"] == "cluster_asset_prices_task"

    cleanup = schedule["cleanup-old-reports-daily"]
    assert cleanup["task"] == "cleanup_old_report_files_task"
    assert cleanup["args"] == (7,)


@pytest.mark.integration
def test_healthcheck_task_registered():
    from services.worker.celery_app import celery_app

    assert "healthcheck" in celery_app.tasks
    result = celery_app.tasks["healthcheck"]()
    assert result == "ok"


@pytest.mark.integration
def test_celery_configuration_values():
    from services.worker.celery_app import celery_app

    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_track_started is True
    assert celery_app.conf.task_time_limit == 600
    assert celery_app.conf.broker_connection_retry_on_startup is True

    assert "WORKERS_QUEUE" in celery_app.amqp.queues


@pytest.mark.integration
def test_redis_connection_local():
    redis_sync_client.connect()
    key = "test:key"
    value = "42"

    redis_sync_client.set(key, value)
    stored_value = redis_sync_client.get(key)
    assert stored_value == value

    redis_sync_client.delete(key)

    if redis_sync_client._client:
        redis_sync_client._client.close()
    redis_sync_client._client = None

import json
import logging
from pathlib import Path

from core.config import settings
from core.report.xls_generator import generate_xls_report
from services.worker.celery_app import celery_app
from services.worker.sync_clients.redis_pubsub import get_pubsub
from services.worker.sync_clients.redis_client import redis_sync_client
from services.worker.sync_clients.kafka_producer import producer_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="report.run_report", ignore_result=True)
def run_report(task_id: str):
    """Execute a report task and publish updates."""

    key = f"report:{task_id}"
    lock_name = f"lock:{key}"

    redis_sync_client.connect()

    with redis_sync_client.lock(lock_name):

        cached = redis_sync_client.hgetall(key)
        if not cached:
            return

        fetched = json.loads(cached.get("fetched_data"))
        simulation_id = fetched["simulation_id"]
        user_id = int(fetched["user_id"])

        file_path = generate_xls_report(task_id, fetched)

        if not file_path or not Path(file_path).exists():
            status = "failed"
            download_url = None
        else:
            status = "done"
            download_url = f"{settings.API_BASE_URL}/tmp/reports/report_{simulation_id}.xls"

        pubsub = get_pubsub("report", task_id)
        pubsub.publish({
            "task_id": task_id,
            "user_id": user_id,
            "status": status,
            "download_url": download_url,
        })
        pubsub.close()

        buf_key = f"buffer:report:{task_id}"
        redis_sync_client.rpush_list(buf_key, json.dumps({
            "task_id": task_id,
            "user_id": user_id,
            "status": "done",
            "download_url": download_url,
        }))
        redis_sync_client.client.expire(buf_key, 900)

    redis_sync_client.delete(key)

    producer_sync.publish_simulation_event(task_id=task_id, stage="run_report", status="done")

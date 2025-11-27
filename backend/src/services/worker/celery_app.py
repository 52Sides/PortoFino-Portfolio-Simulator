from kombu import Queue

from celery import Celery, shared_task

from core.config import settings


celery_app = Celery(
    "portofino",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_time_limit=600,
)

celery_app.conf.task_queues = (
    Queue("WORKERS_QUEUE"),
)

celery_app.autodiscover_tasks([
    "services.worker.tasks.report",
    "services.worker.tasks.simulation",
    "services.worker.tasks.scheduler",
])

celery_app.conf.beat_schedule = {
    "vacuum-every-night": {
        "task": "vacuum_analyze_task",
        "schedule": 60 * 60 * 24,
    },
    "cluster-monthly": {
        "task": "cluster_asset_prices_task",
        "schedule": 60 * 60 * 24 * 30,
    },
    "cleanup-old-reports-daily": {
        "task": "cleanup_old_report_files_task",
        "schedule": 60 * 60 * 24,
        "args": (7,),
    },
}


@shared_task(name="healthcheck")
def healthcheck():
    return "ok"

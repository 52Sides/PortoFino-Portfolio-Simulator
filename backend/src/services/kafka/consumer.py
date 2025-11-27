import json
import logging
import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import settings
from services.worker.tasks.simulation import run_simulation
from services.worker.tasks.report import run_report

logger = logging.getLogger(__name__)

WORKERS_QUEUE = "workers_queue"


async def consume_events():
    """Consume Kafka events and dispatch simulation or report tasks based on topic and stage."""

    consumer = AIOKafkaConsumer(
        settings.KAFKA_SIMULATION_TOPIC,
        settings.KAFKA_REPORT_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id="unified-consumers",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    try:
        await consumer.start()
        logger.info("[Kafka] Consumer started")

        async for msg in consumer:
            try:
                topic = msg.topic
                event = msg.value

                task_id = event.get("task_id")
                stage = event.get("stage")
                status = event.get("status")

                if not task_id or status != "waiting":
                    continue

                if topic == settings.KAFKA_SIMULATION_TOPIC and stage == "run_simulation":
                    run_simulation.apply_async(args=[task_id], queue=WORKERS_QUEUE)

                if topic == settings.KAFKA_REPORT_TOPIC and stage == "run_report":
                    run_report.apply_async(args=[task_id], queue=WORKERS_QUEUE)

            except Exception:
                logger.exception("Kafka consumer event processing failed")

    except asyncio.CancelledError:
        raise

    except Exception:
        logger.exception("Kafka consumer error")

    finally:
        await consumer.stop()

import json
import asyncio

from aiokafka import AIOKafkaProducer

from core.config import settings


class KafkaProducerService:
    """Loop-safe universal Kafka producer."""

    def __init__(self, bootstrap_servers: str = settings.KAFKA_BROKER):
        self.bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def start(self):
        """Initializes AIOKafkaProducer on first use or in a new loop"""
        current_loop = asyncio.get_running_loop()
        if self._producer is None or self._loop != current_loop:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            self._loop = current_loop

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            self._loop = None

    async def send(self, topic: str, message: dict, retries=3):
        for attempt in range(retries):
            try:
                await self.start()
                await self._producer.send_and_wait(topic, message)
                return

            except Exception:
                if attempt == retries - 1:
                    raise

                await asyncio.sleep(0.2 * (attempt + 1))

    async def publish_event(self, topic: str, task_id: str, stage: str, status: str):
        msg = {"task_id": task_id, "stage": stage, "status": status}
        await self.send(topic, msg)

    async def publish_simulation_event(self, **kwargs):
        await self.publish_event(settings.KAFKA_SIMULATION_TOPIC, **kwargs)

    async def publish_report_event(self, **kwargs):
        await self.publish_event(settings.KAFKA_REPORT_TOPIC, **kwargs)


# --- Fast API singleton ---
producer = KafkaProducerService()

import json
import threading

from kafka import KafkaProducer

from core.config import settings


class KafkaProducerSync:
    """Thread-safe Kafka producer for Celery sync workers."""

    _lock = threading.Lock()

    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    def connect(self):
        with self._lock:
            if self._producer is None:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    linger_ms=5,
                )

    def send(self, topic: str, message: dict):
        if self._producer is None:
            self.connect()
        fut = self._producer.send(topic, message)
        fut.get(timeout=10)   # sync wait

    def publish_event(self, topic: str, task_id: str, stage: str, status: str):
        msg = {"task_id": task_id, "stage": stage, "status": status}
        self.send(topic, msg)

    def publish_simulation_event(self, **kwargs):
        self.publish_event(settings.KAFKA_SIMULATION_TOPIC, **kwargs)

    def publish_report_event(self, **kwargs):
        self.publish_event(settings.KAFKA_REPORT_TOPIC, **kwargs)


# Celery singleton (per-process)
producer_sync = KafkaProducerSync(settings.KAFKA_BROKER)

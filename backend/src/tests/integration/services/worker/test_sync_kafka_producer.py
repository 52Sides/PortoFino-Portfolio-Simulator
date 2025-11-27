import pytest
from kafka import KafkaConsumer
from services.worker.sync_clients.kafka_producer import KafkaProducerSync, producer_sync
from core.config import settings

TOPIC_SIM = settings.KAFKA_SIMULATION_TOPIC
TOPIC_REP = settings.KAFKA_REPORT_TOPIC
KAFKA_SERVERS = settings.KAFKA_BROKER.split(",")


def consume_one(topic):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_SERVERS,
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000,
        value_deserializer=lambda v: v.decode("utf-8")
    )
    msgs = [msg.value for msg in consumer]
    consumer.close()
    return msgs


@pytest.mark.integration
def test_connect_and_send():
    p = KafkaProducerSync(KAFKA_SERVERS)
    p.connect()
    assert p._producer is not None

    p.send(TOPIC_SIM, {"test": 123})
    msgs = consume_one(TOPIC_SIM)
    assert any('"test": 123' in m for m in msgs)


@pytest.mark.integration
def test_publish_event_methods():
    p = KafkaProducerSync(KAFKA_SERVERS)

    p.publish_event(TOPIC_REP, "id1", "stage1", "ok")
    msgs = consume_one(TOPIC_REP)
    assert any('"task_id": "id1"' in m and '"stage": "stage1"' in m for m in msgs)

    p.publish_simulation_event(task_id="sim1", stage="start", status="ok")
    msgs = consume_one(TOPIC_SIM)
    assert any('"task_id": "sim1"' in m for m in msgs)

    p.publish_report_event(task_id="rep1", stage="end", status="fail")
    msgs = consume_one(TOPIC_REP)
    assert any('"task_id": "rep1"' in m for m in msgs)


@pytest.mark.integration
def test_singleton_usage():
    producer_sync.publish_simulation_event(task_id="singleton", stage="s", status="ok")
    msgs = consume_one(TOPIC_SIM)
    assert any('"task_id": "singleton"' in m for m in msgs)

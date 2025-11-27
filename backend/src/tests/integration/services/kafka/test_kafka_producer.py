import pytest
import asyncio
import json
import uuid

from aiokafka import AIOKafkaConsumer

from core.config import settings
from services.kafka.producer import KafkaProducerService


async def find_message(consumer: AIOKafkaConsumer, expected_task_id: str, timeout: float = 2.0):
    found = False
    received_data = None
    try:
        async for msg in asyncio.wait_for(consumer, timeout=timeout):
            data = json.loads(msg.value)
            if data.get("task_id") == expected_task_id:
                found = True
                received_data = data
                break

    except asyncio.TimeoutError:
        pass

    return found, received_data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_send_delivers_message():
    topic = "integration-test-send"
    producer = KafkaProducerService()
    await producer.start()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=f"test-send-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode("utf-8"),
    )
    await consumer.start()

    try:
        message = {"task_id": "send1", "stage": "fetch", "status": "waiting"}
        await producer.send(topic, message)

        found = False
        async for msg in consumer:
            data = json.loads(msg.value)
            if data.get("task_id") == "send1":
                found = True
                assert data == message
                break

        assert found, "Expected message not found in Kafka topic"
    finally:
        await producer.stop()
        await consumer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_event_delivers_message():
    topic = "integration-test-publish-event"
    producer = KafkaProducerService()
    await producer.start()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=f"test-publish-event-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode("utf-8"),
    )
    await consumer.start()

    try:
        expected_message = {"task_id": "evt1", "stage": "run", "status": "waiting"}
        await producer.publish_event(topic, **expected_message)

        found = False
        async for msg in consumer:
            data = json.loads(msg.value)
            if data.get("task_id") == expected_message["task_id"]:
                found = True
                assert data == expected_message
                break

        assert found, "Expected message not found in Kafka topic"
    finally:
        await producer.stop()
        await consumer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_simulation_event_delivers_message():
    topic = settings.KAFKA_SIMULATION_TOPIC
    producer = KafkaProducerService()
    await producer.start()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=f"test-publish-sim-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode("utf-8"),
    )
    await consumer.start()

    try:
        expected_message = {"task_id": "sim1", "stage": "simulate", "status": "waiting"}
        await producer.publish_simulation_event(**expected_message)

        found = False
        async for msg in consumer:
            data = json.loads(msg.value)
            if data.get("task_id") == expected_message["task_id"]:
                found = True
                assert data == expected_message
                break

        assert found, "Expected message not found in Kafka topic"
    finally:
        await producer.stop()
        await consumer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_report_event_delivers_message():
    topic = settings.KAFKA_REPORT_TOPIC
    producer = KafkaProducerService()
    await producer.start()

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=f"test-publish-report-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode("utf-8"),
    )
    await consumer.start()

    try:
        expected_message = {"task_id": "rep1", "stage": "report", "status": "waiting"}
        await producer.publish_report_event(**expected_message)

        found = False
        async for msg in consumer:
            data = json.loads(msg.value)
            if data.get("task_id") == expected_message["task_id"]:
                found = True
                assert data == expected_message
                break

        assert found, "Expected message not found in Kafka topic"
    finally:
        await producer.stop()
        await consumer.stop()

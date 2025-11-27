import pytest
from unittest.mock import AsyncMock

from core.config import settings
from services.kafka.producer import KafkaProducerService


@pytest.fixture
def mock_aio_producer(monkeypatch):
    mock = AsyncMock()
    mock.send_and_wait = AsyncMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()

    monkeypatch.setattr("services.kafka.producer.AIOKafkaProducer", lambda *a, **kw: mock)
    return mock


@pytest.fixture
def producer(mock_aio_producer):
    return KafkaProducerService(settings.KAFKA_BROKER)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_initializes_producer_only_once(producer, mock_aio_producer):
    await producer.start()
    first_instance = producer._producer

    await producer.start()
    second_instance = producer._producer

    assert first_instance is second_instance
    mock_aio_producer.start.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stop_clears_producer(producer, mock_aio_producer):
    await producer.start()
    await producer.stop()
    assert producer._producer is None
    mock_aio_producer.stop.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_calls_send_and_wait(producer, mock_aio_producer):
    msg = {"x": 1}
    await producer.send("test-topic", msg)
    mock_aio_producer.send_and_wait.assert_awaited_once_with("test-topic", msg)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_event_calls_send(producer, mock_aio_producer):
    await producer.publish_event("test-topic", task_id="abc", stage="fetch", status="waiting")
    mock_aio_producer.send_and_wait.assert_awaited_once_with(
        "test-topic", {"task_id": "abc", "stage": "fetch", "status": "waiting"}
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_simulation_event_calls_send(producer, mock_aio_producer):
    await producer.publish_simulation_event(task_id="t1", stage="simulate", status="queued")
    mock_aio_producer.send_and_wait.assert_awaited_once_with(
        settings.KAFKA_SIMULATION_TOPIC, {"task_id": "t1", "stage": "simulate", "status": "queued"}
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_report_event_calls_send(producer, mock_aio_producer):
    await producer.publish_report_event(task_id="r1", stage="build", status="waiting")
    mock_aio_producer.send_and_wait.assert_awaited_once_with(
        settings.KAFKA_REPORT_TOPIC, {"task_id": "r1", "stage": "build", "status": "waiting"}
    )

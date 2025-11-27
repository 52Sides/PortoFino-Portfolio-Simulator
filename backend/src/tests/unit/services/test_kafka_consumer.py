import pytest
from unittest.mock import AsyncMock, MagicMock

from services.kafka.consumer import consume_events, WORKERS_QUEUE
from core.config import settings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_process_simulation_event(monkeypatch):
    """Properly processes a run_simulation event."""
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()

    msg = MagicMock()
    msg.topic = settings.KAFKA_SIMULATION_TOPIC
    msg.value = {"task_id": "T1", "stage": "run_simulation", "status": "waiting"}

    async def msg_iter():
        yield msg
        return

    mock_consumer.__aiter__.side_effect = msg_iter

    monkeypatch.setattr(
        "services.kafka.consumer.AIOKafkaConsumer",
        lambda *args, **kwargs: mock_consumer
    )

    mock_run_sim = MagicMock()
    mock_run_sim.apply_async = MagicMock()
    monkeypatch.setattr("services.kafka.consumer.run_simulation", mock_run_sim)
    monkeypatch.setattr("services.kafka.consumer.run_report", MagicMock())

    await consume_events()

    mock_run_sim.apply_async.assert_called_once_with(args=["T1"], queue=WORKERS_QUEUE)
    mock_consumer.stop.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_process_report_event(monkeypatch):
    """Properly processes a run_report event."""
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()

    msg = MagicMock()
    msg.topic = settings.KAFKA_REPORT_TOPIC
    msg.value = {"task_id": "R5", "stage": "run_report", "status": "waiting"}

    async def msg_iter():
        yield msg

    mock_consumer.__aiter__.side_effect = msg_iter

    monkeypatch.setattr(
        "services.kafka.consumer.AIOKafkaConsumer",
        lambda *args, **kwargs: mock_consumer
    )

    mock_run_report = MagicMock()
    mock_run_report.apply_async = MagicMock()
    monkeypatch.setattr("services.kafka.consumer.run_report", mock_run_report)
    monkeypatch.setattr("services.kafka.consumer.run_simulation", MagicMock())

    await consume_events()

    mock_run_report.apply_async.assert_called_once_with(args=["R5"], queue=WORKERS_QUEUE)
    mock_consumer.stop.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_ignores_invalid_events(monkeypatch):
    """Events without task_id or with status != waiting are ignored."""
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()

    events = [
        {"task_id": None, "stage": "run_simulation", "status": "waiting"},
        {"task_id": "X", "stage": "run_simulation", "status": "done"},
    ]

    async def msg_iter():
        for e in events:
            m = MagicMock()
            m.topic = settings.KAFKA_SIMULATION_TOPIC
            m.value = e
            yield m

    mock_consumer.__aiter__.side_effect = msg_iter

    monkeypatch.setattr("services.kafka.consumer.AIOKafkaConsumer",
                        lambda *args, **kwargs: mock_consumer)

    mock_sim = MagicMock()
    mock_sim.apply_async = MagicMock()
    monkeypatch.setattr("services.kafka.consumer.run_simulation", mock_sim)
    monkeypatch.setattr("services.kafka.consumer.run_report", MagicMock())

    await consume_events()

    mock_sim.apply_async.assert_not_called()
    mock_consumer.stop.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_handles_event_processing_error(monkeypatch):
    """Errors during event processing are logged, loop continues."""
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()

    msg = MagicMock()
    msg.topic = settings.KAFKA_SIMULATION_TOPIC
    msg.value = {"task_id": "ERR", "stage": "run_simulation", "status": "waiting"}

    async def msg_iter():
        yield msg
        return

    mock_consumer.__aiter__.side_effect = msg_iter

    monkeypatch.setattr("services.kafka.consumer.AIOKafkaConsumer",
                        lambda *args, **kwargs: mock_consumer)

    mock_run_sim = MagicMock()
    mock_run_sim.apply_async = MagicMock(side_effect=RuntimeError("fail"))
    monkeypatch.setattr("services.kafka.consumer.run_simulation", mock_run_sim)
    monkeypatch.setattr("services.kafka.consumer.run_report", MagicMock())

    await consume_events()

    mock_consumer.stop.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_top_level_exception(monkeypatch):
    """Exceptions in consumer.start() are caught and finally stops the consumer."""
    mock_consumer = MagicMock()
    mock_consumer.start = AsyncMock(side_effect=RuntimeError("startup error"))
    mock_consumer.stop = AsyncMock()

    monkeypatch.setattr("services.kafka.consumer.AIOKafkaConsumer", lambda *args, **kwargs: mock_consumer)

    await consume_events()

    mock_consumer.stop.assert_awaited()

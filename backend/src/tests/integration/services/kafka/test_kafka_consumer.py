import pytest
import asyncio

from unittest.mock import patch
from aiokafka import AIOKafkaProducer

from core.config import settings
from services.kafka.consumer import consume_events

CONSUMER_WAIT = 1.0


async def send_event(event_json: str, topic: str):
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BROKER,
        value_serializer=lambda v: v.encode("utf-8"),
    )
    await producer.start()
    try:
        await producer.send_and_wait(topic, event_json)
    finally:
        await producer.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_ignores_event_without_task_id():
    event = '{"stage":"run_simulation","status":"waiting"}'

    with patch("services.kafka.consumer.run_simulation.apply_async") as mock_sim:
        consumer_task = asyncio.create_task(consume_events())
        await send_event(event, settings.KAFKA_SIMULATION_TOPIC)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_sim.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_ignores_event_with_wrong_status():
    event = '{"task_id":"x1","stage":"run_simulation","status":"done"}'

    with patch("services.kafka.consumer.run_simulation.apply_async") as mock_sim:
        consumer_task = asyncio.create_task(consume_events())
        await send_event(event, settings.KAFKA_SIMULATION_TOPIC)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_sim.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_ignores_wrong_stage_for_simulation_topic():
    event = '{"task_id":"x2","stage":"unknown_stage","status":"waiting"}'

    with patch("services.kafka.consumer.run_simulation.apply_async") as mock_sim:
        consumer_task = asyncio.create_task(consume_events())
        await send_event(event, settings.KAFKA_SIMULATION_TOPIC)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_sim.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_ignores_wrong_stage_for_report_topic():
    event = '{"task_id":"x3","stage":"unknown_stage","status":"waiting"}'

    with patch("services.kafka.consumer.run_report.apply_async") as mock_report:
        consumer_task = asyncio.create_task(consume_events())
        await send_event(event, settings.KAFKA_REPORT_TOPIC)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_report.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task


@pytest.mark.integration
@pytest.mark.asyncio
async def test_consumer_wrong_topic_stage_combination():
    event = '{"task_id":"x4","stage":"run_simulation","status":"waiting"}'

    with patch("services.kafka.consumer.run_simulation.apply_async") as mock_sim, \
         patch("services.kafka.consumer.run_report.apply_async") as mock_report:

        consumer_task = asyncio.create_task(consume_events())
        await send_event(event, settings.KAFKA_REPORT_TOPIC)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_sim.assert_not_called()
        mock_report.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topic,event_json",
    [
        (settings.KAFKA_SIMULATION_TOPIC, '{"task_id": "s2", "stage": "unknown_stage", "status": "waiting"}'),
        (settings.KAFKA_REPORT_TOPIC, '{"task_id": "r2", "stage": "run_report", "status": "done"}'),
    ],
)
async def test_consumer_ignores_unexpected_events(topic, event_json):
    with patch("services.kafka.consumer.run_simulation.apply_async") as mock_sim, \
         patch("services.kafka.consumer.run_report.apply_async") as mock_report:

        consumer_task = asyncio.create_task(consume_events())
        await send_event(event_json, topic)
        await asyncio.sleep(CONSUMER_WAIT)

        mock_sim.assert_not_called()
        mock_report.assert_not_called()

        consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer_task

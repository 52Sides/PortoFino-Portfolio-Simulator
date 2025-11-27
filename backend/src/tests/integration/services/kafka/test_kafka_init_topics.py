import pytest
import asyncio

from aiokafka.admin import AIOKafkaAdminClient

from core.config import settings
from services.kafka.init_topics import create_topics, TOPICS


async def wait_until_deleted(admin: AIOKafkaAdminClient, topics: list[str], timeout=15):
    for _ in range(timeout * 60):
        existing = await admin.list_topics()
        if all(t not in existing for t in topics):
            return

        await asyncio.sleep(0.1)
    raise TimeoutError(f"Topics not deleted in time: {topics}")


async def wait_until_created(admin: AIOKafkaAdminClient, topics: list[str], timeout=20):
    for _ in range(timeout * 10):
        meta = await admin.describe_topics(topics)
        if all(m.get("error_code") == 0 for m in meta):
            return

        await asyncio.sleep(0.3)
    raise TimeoutError(str([(m["topic"], m["error_code"]) for m in meta]))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_topics_creates_missing_topics():
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BROKER)
    await admin.start()

    try:
        existing_topics = await admin.list_topics()
        to_delete = [t["name"] for t in TOPICS if t["name"] in existing_topics]

        if to_delete:
            await admin.delete_topics(to_delete)
            await wait_until_deleted(admin, to_delete)

        existing_topics = await admin.list_topics()
        for t in TOPICS:
            assert t["name"] not in existing_topics

        await create_topics()
        await admin.list_topics()
        await wait_until_created(admin, [t["name"] for t in TOPICS])

        existing_topics = await admin.list_topics()
        for t in TOPICS:
            assert t["name"] in existing_topics

    finally:
        await admin.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_topics_idempotent():
    await create_topics()
    await create_topics()

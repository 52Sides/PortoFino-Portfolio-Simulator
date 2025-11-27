import logging

from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from core.config import settings

logger = logging.getLogger(__name__)

TOPICS = [
    {"name": "simulation-events", "num_partitions": 1, "replication_factor": 1},
    {"name": "report-events", "num_partitions": 1, "replication_factor": 1},
]


async def create_topics():
    """Create required Kafka topics if they do not already exist."""

    admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BROKER)

    await admin.start()
    try:
        existing = await admin.list_topics()
        to_create = [NewTopic(**t) for t in TOPICS if t["name"] not in existing]

        if to_create:
            await admin.create_topics(new_topics=to_create, validate_only=False)
            logger.info(f"Created Kafka topics: {[t.name for t in to_create]}")
        else:
            logger.info("Kafka topics already exist")

    finally:
        await admin.close()

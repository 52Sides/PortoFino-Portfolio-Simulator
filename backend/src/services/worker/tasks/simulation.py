import json
import logging
from io import StringIO

import pandas as pd

from core.simulation.portfolio_simulator import PortfolioSimulator
from schemas.simulation import ParsedCommandModel, SimulateResponseWS
from services.worker.celery_app import celery_app
from services.worker.sync_clients.redis_pubsub import get_pubsub
from services.worker.sync_clients.database import get_sync_db
from services.worker.sync_clients.redis_client import redis_sync_client
from services.worker.sync_clients.kafka_producer import producer_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="simulation.run_simulation", ignore_result=True)
def run_simulation(task_id: str):
    """Execute a portfolio simulation task, store results, and publish updates."""

    key = f"simulation:{task_id}"
    lock_name = f"lock:{key}"

    redis_sync_client.connect()

    with redis_sync_client.lock(lock_name):

        cached = redis_sync_client.hgetall(key)
        if not cached:
            return

        command = cached["command"]
        user_id = int(cached["user_id"])
        parsed = ParsedCommandModel.model_validate_json(cached["parsed_command"])
        logger.info(f"[Worker] Parsed command: {parsed}")

        combined_df = pd.read_json(StringIO(cached["combined_df"]), orient="records")
        logger.info(f"[Worker] Combined DF rows={len(combined_df)}")

        simulator = PortfolioSimulator(command, parsed, combined_df, user_id)
        result = simulator.run()
        logger.info(f"[Worker] Simulation completed for user={user_id}, task={task_id}")

        with get_sync_db() as db:
            db.add(result)
            db.commit()

        response = SimulateResponseWS(
            cagr=result.cagr,
            sharpe=result.sharpe,
            max_drawdown=result.max_drawdown,
            portfolio_value=result.portfolio_value
        )
        logger.info(f"[Worker] Portfolio value points: {len(result.portfolio_value)}")

        pubsub = get_pubsub("simulation", task_id)
        pubsub.publish({
            "task_id": task_id,
            "user_id": user_id,
            "status": "done",
            "data": response.model_dump(),
        })
        pubsub.close()

        buf_key = f"buffer:simulation:{task_id}"
        redis_sync_client.rpush_list(buf_key, json.dumps({
            "task_id": task_id,
            "user_id": user_id,
            "status": "done",
            "data": response.model_dump(),
        }))
        redis_sync_client.client.expire(buf_key, 900)

    redis_sync_client.delete(key)

    producer_sync.publish_simulation_event(task_id=task_id, stage="run_simulation", status="done")
    logger.info(f"[Worker] Simulation task finished: task_id={task_id}")

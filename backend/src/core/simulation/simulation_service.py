from uuid import uuid4

from core.simulation.command_parser import safe_command_parse, CommandValidationError
from core.simulation.data_preparator import DataPreparator
from db.database import AsyncSessionLocal
from schemas.simulation import SimulateResponse
from services.kafka.producer import producer
from services.redis.client import redis_client


class SimulationService:
    """Simulation Management Service"""

    @staticmethod
    async def create_simulation(command: str, user_id: int) -> SimulateResponse:
        """Initiates a portfolio simulation task with immediate command validation."""
        try:
            parsed_command = await safe_command_parse(command)
        except CommandValidationError as e:
            raise ValueError(f"Invalid command: {e}")

        task_id = str(uuid4())

        async with AsyncSessionLocal() as db:
            combined_df = await DataPreparator.collect_portfolio_data(parsed_command, db)

        mapping = {
            "command": command,
            "user_id": user_id,
            "parsed_command": parsed_command.model_dump_json(),
            "combined_df": combined_df.to_json(orient="records", date_format="iso")
        }
        await redis_client.hset(f"simulation:{task_id}", mapping=mapping)

        await producer.publish_simulation_event(task_id=task_id, stage="run_simulation", status="waiting")

        return SimulateResponse(task_id=task_id)

import json
from uuid import uuid4

from fastapi import HTTPException

from db.database import AsyncSessionLocal
from db.repositories.history_repo import SimHistoryRepo
from schemas.report import ReportResponse
from services.kafka.producer import producer
from services.redis.client import redis_client


def dict_to_list(d: dict):
    if not isinstance(d, dict):
        return []
    return [
        {"date": k, "value": v}
        for k, v in sorted(d.items(), key=lambda x: x[0])
    ]


class ReportService:
    """Service for managing report creation"""

    @staticmethod
    async def create_report(simulation_id: int, user_id: int) -> ReportResponse:
        """Initiates report generation."""

        task_id = str(uuid4())

        async with AsyncSessionLocal() as db:
            sim = await SimHistoryRepo.get_full_sim_history(db, user_id, simulation_id)

        if not sim:
            raise HTTPException(status_code=404, detail="Report not found")

        sim_dict = {
            "simulation_id": sim.id,
            "command": sim.command,
            "tickers": sim.tickers,
            "weights": sim.weights,
            "sides": sim.sides,
            "start_date": sim.start_date.isoformat(),
            "end_date": sim.end_date.isoformat(),

            "portfolio_value": dict_to_list(sim.portfolio_value),
            "daily_returns": dict_to_list(sim.daily_returns),
            "cumulative_returns": dict_to_list(sim.cumulative_returns),

            "cagr": sim.cagr,
            "sharpe": sim.sharpe,
            "max_drawdown": sim.max_drawdown,
            "created_at": sim.created_at.isoformat() if sim.created_at else None,
            "user_id": sim.user_id,
        }

        mapping = {"fetched_data": json.dumps(sim_dict)}
        await redis_client.hset(f"report:{task_id}", mapping=mapping)

        await producer.publish_report_event(task_id=task_id, stage="run_report", status="waiting")

        return ReportResponse(task_id=task_id)

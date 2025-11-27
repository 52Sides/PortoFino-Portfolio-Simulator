from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SimulationModel


class SimHistoryRepo:

    @staticmethod
    async def get_full_sim_history(db: AsyncSession, user_id: int, simulation_id: int):
        """Return full simulation record for given user and simulation ID."""

        stmt = select(SimulationModel).where(
            SimulationModel.id == simulation_id,
            SimulationModel.user_id == user_id
        )
        result = await db.execute(stmt)
        sim_data = result.scalar_one_or_none()

        return sim_data

    @staticmethod
    async def get_light_sim_history(db: AsyncSession, user_id: int, simulation_id: int):
        """Return lightweight simulation data with sorted portfolio values."""

        stmt = select(SimulationModel).where(
            SimulationModel.id == simulation_id,
            SimulationModel.user_id == user_id
        )
        result = await db.execute(stmt)
        sim_data = result.scalar_one_or_none()

        if not sim_data:
            return None

        sorted_dict = dict(sorted(sim_data.portfolio_value.items(), key=lambda x: x[0]))

        return {
            "id": sim_data.id,
            "user_id": sim_data.user_id,
            "command": sim_data.command,
            "cagr": sim_data.cagr,
            "sharpe": sim_data.sharpe,
            "max_drawdown": sim_data.max_drawdown,
            "portfolio_value": sorted_dict,
            "created_at": sim_data.created_at,
        }

    @staticmethod
    async def get_sim_list_by_userid_paginated(db: AsyncSession, user_id: int, page: int, page_size: int):
        """Return total count and paginated list of user simulations."""

        total_stmt = select(func.count(SimulationModel.id)).where(SimulationModel.user_id == user_id)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        stmt = (
            select(
                SimulationModel.id,
                SimulationModel.user_id,
                SimulationModel.command,
                SimulationModel.cagr,
                SimulationModel.sharpe,
                SimulationModel.max_drawdown,
                SimulationModel.created_at,
            )
            .where(SimulationModel.user_id == user_id)
            .order_by(SimulationModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        rows = result.all()
        sims = [
            {
                "id": r.id,
                "user_id": r.user_id,
                "command": r.command,
                "cagr": r.cagr,
                "sharpe": r.sharpe,
                "max_drawdown": r.max_drawdown,
                "created_at": r.created_at,
            }
            for r in rows
        ]
        return total, sims

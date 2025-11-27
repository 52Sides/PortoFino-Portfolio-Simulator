from fastapi import HTTPException

from db.database import AsyncSessionLocal
from db.repositories.history_repo import SimHistoryRepo
from schemas.history import SimHistoryDetail, SimHistoryMetrics, PaginatedSimHistoryList


class HistoryService:
    """Service to fetch and cache user simulation history."""

    @staticmethod
    async def get_sim_history_list(user_id: int, page: int, page_size: int) -> PaginatedSimHistoryList:
        async with AsyncSessionLocal() as db:
            total, sim_histories = await SimHistoryRepo.get_sim_list_by_userid_paginated(db, user_id, page, page_size)

        return PaginatedSimHistoryList(
            total=total,
            page=page,
            page_size=page_size,
            root=[SimHistoryMetrics(**sim) for sim in sim_histories],
        )

    @staticmethod
    async def get_sim_history_detail(user_id: int, simulation_id: int) -> SimHistoryDetail:
        async with AsyncSessionLocal() as db:
            sim_history = await SimHistoryRepo.get_light_sim_history(db, user_id, simulation_id)

            if not sim_history:
                raise HTTPException(status_code=404, detail="Simulation not found")

        return SimHistoryDetail(**sim_history)

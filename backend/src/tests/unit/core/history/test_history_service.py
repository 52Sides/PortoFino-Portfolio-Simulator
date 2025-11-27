import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from core.history.history_service import HistoryService
from schemas.history import SimHistoryDetail, PaginatedSimHistoryList


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sim_history_detail_success():
    mock_repo = AsyncMock()
    mock_repo.get_light_sim_history.return_value = {
        "id": 101,
        "user_id": 1,
        "command": "TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01",
        "cagr": 0.12,
        "sharpe": 1.5,
        "max_drawdown": 0.05,
        "portfolio_value": {"2020-01-01": 1000.0},
        "created_at": datetime(2020, 1, 1),
    }

    class AsyncContextManager:

        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch("core.history.history_service.AsyncSessionLocal", return_value=AsyncContextManager()), \
         patch("db.repositories.history_repo.SimHistoryRepo.get_light_sim_history", mock_repo.get_light_sim_history):

        result = await HistoryService.get_sim_history_detail(user_id=1, simulation_id=101)

    assert isinstance(result, SimHistoryDetail)
    assert result.id == 101
    assert result.portfolio_value["2020-01-01"] == 1000.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sim_history_detail_not_found():

    class AsyncContextManager:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            pass

    async def mock_get_light_sim_history(db, user_id, simulation_id):
        return None

    with patch("core.history.history_service.AsyncSessionLocal", return_value=AsyncContextManager()), \
         patch("db.repositories.history_repo.SimHistoryRepo.get_light_sim_history", mock_get_light_sim_history):

        with pytest.raises(HTTPException):
            await HistoryService.get_sim_history_detail(user_id=1, simulation_id=999)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sim_history_list_success():
    mock_repo = AsyncMock()
    mock_repo.get_sim_list_by_userid_paginated.return_value = (
        2,
        [
            {
                "id": 1, "user_id": 1, "command": "cmd1", "cagr": 0.1,
                "sharpe": 1.0, "max_drawdown": 0.01, "created_at": datetime(2024, 1, 1)
            },
            {
                "id": 2, "user_id": 1, "command": "cmd2", "cagr": 0.2,
                "sharpe": 1.1, "max_drawdown": 0.02, "created_at": datetime(2024, 1, 2)
            },
        ]
    )

    class AsyncContextManager:
        async def __aenter__(self):
            return None

        async def __aexit__(self, exc_type, exc, tb):
            pass

    with patch(
            "core.history.history_service.AsyncSessionLocal",
            return_value=AsyncContextManager()
    ), patch(
        "db.repositories.history_repo.SimHistoryRepo.get_sim_list_by_userid_paginated",
        mock_repo.get_sim_list_by_userid_paginated
    ):
        result = await HistoryService.get_sim_history_list(user_id=1, page=1, page_size=10)

    assert isinstance(result, PaginatedSimHistoryList)
    assert result.total == 2
    assert len(result.root) == 2
    assert result.root[0].id == 1
    assert result.root[1].command == "cmd2"

import pytest
from unittest.mock import MagicMock

from db.repositories.history_repo import SimHistoryRepo


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_full_sim_history_none(mock_db):
    """Return None if simulation is not found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await SimHistoryRepo.get_full_sim_history(mock_db, user_id=1, simulation_id=42)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_full_sim_history_found(mock_db):
    """Return the simulation object if found."""
    fake_obj = MagicMock(id=1, user_id=123)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_obj
    mock_db.execute.return_value = mock_result

    result = await SimHistoryRepo.get_full_sim_history(mock_db, user_id=123, simulation_id=1)
    assert result == fake_obj


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_light_sim_history_none(mock_db):
    """Return None for light version if simulation not found."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await SimHistoryRepo.get_light_sim_history(mock_db, user_id=1, simulation_id=42)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_light_sim_history_found(mock_db):
    """Return a dict with light info if simulation is found."""
    fake_obj = MagicMock(
        id=1, user_id=10, command="run A",
        cagr=5.0, sharpe=1.2, max_drawdown=-0.1,
        portfolio_value={"2024-01-01": 100000},
        created_at="2024-01-01"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_obj
    mock_db.execute.return_value = mock_result

    result = await SimHistoryRepo.get_light_sim_history(mock_db, user_id=10, simulation_id=1)

    assert isinstance(result, dict)
    assert result["id"] == 1
    assert result["user_id"] == 10
    assert result["command"] == "run A"
    assert result["cagr"] == 5.0
    assert result["sharpe"] == 1.2
    assert result["max_drawdown"] == -0.1

    pv = result["portfolio_value"]
    assert isinstance(pv, dict)
    assert "2024-01-01" in pv
    assert pv["2024-01-01"] == 100000


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sim_list_paginated_empty(mock_db):
    """Return total=0 and empty list if no simulations exist."""
    total_result = MagicMock()
    total_result.scalar.return_value = 0

    list_result = MagicMock()
    list_result.all.return_value = []

    mock_db.execute.side_effect = [total_result, list_result]

    total, sims = await SimHistoryRepo.get_sim_list_by_userid_paginated(
        mock_db, user_id=10, page=1, page_size=20
    )

    assert total == 0
    assert sims == []
    assert list_result.all.called


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sim_list_paginated_items(mock_db):
    """Return correct total and serialized rows if simulations exist."""
    total_result = MagicMock()
    total_result.scalar.return_value = 3

    row1 = MagicMock(
        id=1, user_id=10, command="A", cagr=1.1, sharpe=0.5,
        max_drawdown=-0.2, created_at="2024-01-10"
    )
    row2 = MagicMock(
        id=2, user_id=10, command="B", cagr=2.0, sharpe=0.8,
        max_drawdown=-0.1, created_at="2024-01-09"
    )

    list_result = MagicMock()
    list_result.all.return_value = [row1, row2]

    mock_db.execute.side_effect = [total_result, list_result]

    total, sims = await SimHistoryRepo.get_sim_list_by_userid_paginated(
        mock_db, user_id=10, page=1, page_size=20
    )

    assert total == 3
    assert len(sims) == 2
    assert sims[0]["id"] == 1
    assert sims[0]["command"] == "A"
    assert sims[0]["created_at"] == "2024-01-10"
    assert sims[1]["id"] == 2
    assert sims[1]["command"] == "B"
    assert sims[1]["created_at"] == "2024-01-09"

import pytest

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from api.main import app
from api.dependencies.users import get_current_user
from core.history.history_service import HistoryService
from db.models.user_model import UserModel
from schemas.history import SimHistoryMetrics, PaginatedSimHistoryList, SimHistoryDetail

FULL_SIM_DATA = {
    "id": 101,
    "user_id": 42,
    "command": "TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01",
    "cagr": 0.12,
    "sharpe": 1.5,
    "max_drawdown": 0.05,
    "portfolio_value": {"2020-01-01": 1000.0, "2020-01-02": 1010.0},
    "created_at": "2020-01-01T00:00:00"
}


@pytest.fixture
def client(monkeypatch):
    """TestClient with mocked dependencies"""

    async def fake_user():
        return UserModel(id=42, email="test@example.com")

    app.dependency_overrides[get_current_user] = fake_user

    monkeypatch.setattr(
        HistoryService,
        "get_sim_history_list",
        AsyncMock(return_value=PaginatedSimHistoryList(
            total=1,
            page=1,
            page_size=20,
            root=[SimHistoryMetrics(**FULL_SIM_DATA)]
        ))
    )

    monkeypatch.setattr(
        HistoryService,
        "get_sim_history_detail",
        AsyncMock(return_value=SimHistoryDetail(**FULL_SIM_DATA))
    )

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_list_simulations_history_endpoint(client):
    response = client.get("/history/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert isinstance(data["root"], list)
    assert data["root"][0]["id"] == FULL_SIM_DATA["id"]
    assert data["root"][0]["user_id"] == FULL_SIM_DATA["user_id"]
    assert data["root"][0]["command"] == FULL_SIM_DATA["command"]
    assert data["root"][0]["cagr"] == FULL_SIM_DATA["cagr"]
    assert data["root"][0]["sharpe"] == FULL_SIM_DATA["sharpe"]
    assert data["root"][0]["max_drawdown"] == FULL_SIM_DATA["max_drawdown"]
    assert data["root"][0]["created_at"] == FULL_SIM_DATA["created_at"]


@pytest.mark.unit
def test_get_simulation_history_endpoint(client):
    response = client.get("/history/101")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 101


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_simulation_history_not_found(test_client, monkeypatch):
    async def fake_user():
        return UserModel(id=42, email="test@example.com")

    app.dependency_overrides[get_current_user] = fake_user

    monkeypatch.setattr(
        HistoryService,
        "get_sim_history_detail",
        AsyncMock(side_effect=Exception("Simulation not found"))
    )

    response = await test_client.get("/history/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Simulation not found"}

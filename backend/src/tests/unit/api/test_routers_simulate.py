import pytest

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from api.main import app
from api.dependencies.users import get_current_user
from core.simulation.simulation_service import SimulationService
from db.models.user_model import UserModel
from schemas.simulation import SimulateResponse


@pytest.fixture
def client(monkeypatch):
    async def fake_user():
        return UserModel(id=42, email="test@example.com")

    app.dependency_overrides[get_current_user] = fake_user

    monkeypatch.setattr(
        SimulationService,
        "create_simulation",
        AsyncMock(return_value=SimulateResponse(task_id="abc123", status="queued"))
    )

    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_simulate_valid_command(client):
    response = client.post("/simulate/", json={"command": "TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01"})
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "abc123"
    assert data["status"] == "queued"


@pytest.mark.unit
def test_simulate_invalid_command(client, monkeypatch):
    monkeypatch.setattr(
        SimulationService,
        "create_simulation",
        AsyncMock(side_effect=ValueError("Invalid command: BADCOMMAND"))
    )

    response = client.post("/simulate/", json={"command": "BADCOMMAND"})
    assert response.status_code == 400
    data = response.json()
    assert "Invalid command" in data["detail"]

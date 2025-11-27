import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from uuid import UUID

from api.main import app
from api.dependencies.users import get_current_user
from core.report.report_service import ReportService, dict_to_list
from db.models.user_model import UserModel
from db.models.simulation_model import SimulationModel
from schemas.report import ReportResponse


@pytest.fixture
def simulation_obj():
    """Create a real SimulationModel ORM instance without a database."""
    sim = SimulationModel(
        id=10,
        user_id=42,
        command="TSLA-L-50% NVDA-L-50%",
        tickers={"TSLA": 0.5, "NVDA": 0.5},
        weights={"TSLA": 0.5, "NVDA": 0.5},
        sides={"TSLA": "L", "NVDA": "L"},
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2020, 12, 31),
        cagr=0.25,
        sharpe=1.7,
        max_drawdown=-0.15,
        portfolio_value={"2020-01-02": 100000},
        daily_returns={"2020-01-02": 0.01},
        cumulative_returns={"2020-01-02": 1.01},
        created_at=datetime.datetime(2020, 12, 31, 12, 0, 0),
    )
    return sim


@pytest.fixture
def client(monkeypatch):
    async def fake_user():
        return UserModel(id=42, email="test@example.com")

    app.dependency_overrides[get_current_user] = fake_user

    monkeypatch.setattr(
        ReportService,
        "create_report",
        AsyncMock(return_value=ReportResponse(task_id="rpt123"))
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_create_report_endpoint(client):
    request_data = {"simulation_id": 123}
    response = client.post("/report/", json=request_data)

    assert response.status_code == 200
    data = response.json()
    model = ReportResponse(**data)
    assert isinstance(model, ReportResponse)
    assert model.task_id == "rpt123"


@pytest.mark.unit
def test_create_report_invalid_simulation_id(client):
    request_data = {"simulation_id": "BAD"}
    response = client.post("/report/", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_report_success(simulation_obj, monkeypatch):
    """Verify the full workflow of ReportService.create_report."""

    fake_session_ctx = MagicMock()
    fake_session_ctx.__aenter__.return_value = MagicMock()
    fake_session_ctx.__aexit__.return_value = False
    monkeypatch.setattr(
        "core.report.report_service.AsyncSessionLocal",
        lambda: fake_session_ctx
    )

    async def fake_get_history(db, uid, sid):
        return simulation_obj

    monkeypatch.setattr(
        "core.report.report_service.SimHistoryRepo.get_full_sim_history",
        fake_get_history
    )

    mock_redis = AsyncMock()
    monkeypatch.setattr("core.report.report_service.redis_client", mock_redis)

    mock_producer = AsyncMock()
    monkeypatch.setattr("core.report.report_service.producer", mock_producer)

    resp: ReportResponse = await ReportService.create_report(simulation_id=10, user_id=42)

    assert isinstance(resp, ReportResponse)
    assert isinstance(UUID(resp.task_id), UUID)

    mock_redis.hset.assert_awaited_once()
    args, kwargs = mock_redis.hset.call_args
    assert args[0].startswith("report:")
    assert "fetched_data" in kwargs["mapping"]

    mock_producer.publish_report_event.assert_awaited_once()
    _, kwargs = mock_producer.publish_report_event.call_args
    assert kwargs["status"] == "waiting"
    assert kwargs["stage"] == "run_report"
    assert UUID(kwargs["task_id"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_report_not_found(monkeypatch):
    """Verify 404 is raised when the simulation does not exist."""

    fake_session_ctx = MagicMock()
    fake_session_ctx.__aenter__.return_value = MagicMock()
    monkeypatch.setattr(
        "core.report.report_service.AsyncSessionLocal",
        lambda: fake_session_ctx
    )

    async def fake_not_found(db, uid, sid):
        return None

    monkeypatch.setattr(
        "core.report.report_service.SimHistoryRepo.get_full_sim_history",
        fake_not_found
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        await ReportService.create_report(10, 42)

    assert e.value.status_code == 404


@pytest.mark.unit
def test_dict_to_list_normalizes_properly():
    data = {"2020-01-02": 2, "2020-01-01": 1}
    result = dict_to_list(data)

    assert result == [
        {"date": "2020-01-01", "value": 1},
        {"date": "2020-01-02", "value": 2},
    ]


@pytest.mark.unit
def test_dict_to_list_non_dict():
    assert dict_to_list(None) == []
    assert dict_to_list(123) == []

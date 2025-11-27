import pytest_asyncio
import pytest
import warnings
from unittest.mock import AsyncMock, MagicMock

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from api.main import app
from db.database import Base, get_db


def pytest_configure():
    warnings.filterwarnings("ignore", category=ResourceWarning)


@pytest.fixture(autouse=True)
def restore_history_service(monkeypatch):
    from core.history import history_service
    from core.history.history_service import HistoryService

    monkeypatch.setattr(
        history_service.HistoryService,
        "get_sim_history_detail",
        HistoryService.__dict__['get_sim_history_detail']
    )


@pytest.fixture
def mock_db():
    """SQLAlchemy mocked session"""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _get_test_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield async_session
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client(async_test_db):
    """Client for queries in the test application. Works with an in-memory database."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def async_client():
    """Async HTTP client для реального backend"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture
def mock_pubsub(monkeypatch):

    class MockedPubSub:
        def __init__(self, *, events=None, error=None):
            self.events = events or []
            self.error = error

        async def subscribe(self):
            if self.error:
                raise self.error
            for e in self.events:
                yield e

        async def close(self):
            pass

    def factory(*args, events=None, error=None, **kwargs):
        return MockedPubSub(events=events, error=error)

    monkeypatch.setattr("api.routers.ws_reports.get_pubsub", factory)
    monkeypatch.setattr("api.routers.ws_simulations.get_pubsub", factory)

    return factory


@pytest.fixture
def mock_redis(monkeypatch):
    mock_client = AsyncMock()
    mock_client.hset = AsyncMock()
    mock_client.hgetall = AsyncMock(return_value={})
    mock_client.set = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.delete = AsyncMock()
    mock_client.lock = AsyncMock()
    mock_client.unlock = AsyncMock()
    mock_client.rpush_list = AsyncMock()
    mock_client.lrange_list = AsyncMock()

    mock_redis_client = MagicMock()
    mock_redis_client.hset = mock_client.hset
    mock_redis_client.hgetall = mock_client.hgetall
    mock_redis_client.set = mock_client.set
    mock_redis_client.get = mock_client.get
    mock_redis_client.delete = mock_client.delete
    mock_redis_client.lock = mock_client.lock
    mock_redis_client.unlock = mock_client.unlock
    mock_redis_client.rpush_list = mock_client.rpush_list
    mock_redis_client.lrange_list = mock_client.lrange_list
    mock_redis_client.connect = AsyncMock()
    mock_redis_client.close = AsyncMock()
    mock_redis_client._client = mock_client
    mock_redis_client._connected = True

    monkeypatch.setattr("services.redis.client.redis_client", mock_redis_client)
    monkeypatch.setattr("core.simulation.simulation_service.redis_client", mock_redis_client)
    monkeypatch.setattr("core.report.report_service.redis_client", mock_redis_client)
    monkeypatch.setattr("api.routers.ws_reports.redis_client", mock_redis_client)
    monkeypatch.setattr("api.routers.ws_simulations.redis_client", mock_redis_client)

    return mock_redis_client

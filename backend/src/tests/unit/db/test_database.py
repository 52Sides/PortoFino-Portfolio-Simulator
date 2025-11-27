import pytest
from unittest.mock import AsyncMock

from db import database


@pytest.mark.unit
@pytest.mark.asyncio
async def test_init_db_creates_all(monkeypatch):
    mock_conn = AsyncMock()
    ctx = AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
    monkeypatch.setattr(database, "engine", type("E", (), {"begin": lambda self: ctx})())

    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    mock_conn.run_sync.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_drop_db_drops_all(monkeypatch):
    mock_conn = AsyncMock()
    ctx = AsyncMock(__aenter__=AsyncMock(return_value=mock_conn))
    monkeypatch.setattr(database, "engine", type("E", (), {"begin": lambda self: ctx})())

    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)

    mock_conn.run_sync.assert_awaited_once()

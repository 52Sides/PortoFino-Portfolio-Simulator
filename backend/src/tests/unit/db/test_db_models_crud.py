from datetime import date, datetime
import pytest

from db.models.assets_model import AssetsModel
from db.models.user_model import UserModel
from db.models.refresh_token_model import RefreshTokenModel
from db.models.simulation_model import SimulationModel


@pytest.mark.unit
@pytest.mark.asyncio
async def test_assets_crud(db_session):
    asset = AssetsModel(
        ticker="AAPL",
        date=date(2021, 1, 1),
        open=100,
        high=101,
        low=99,
        close=100,
        volume=1000
    )
    db_session.add(asset)
    await db_session.commit()

    fetched = await db_session.get(AssetsModel, asset.id)
    assert fetched.ticker == "AAPL"

    await db_session.delete(fetched)
    await db_session.commit()
    assert await db_session.get(AssetsModel, asset.id) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_crud(db_session):
    user = UserModel(email="user@test.com", hashed_password="hashedpass")
    db_session.add(user)
    await db_session.commit()

    fetched = await db_session.get(UserModel, user.id)
    assert fetched.email == "user@test.com"

    fetched.hashed_password = "newhash"
    await db_session.commit()
    updated = await db_session.get(UserModel, user.id)
    assert updated.hashed_password == "newhash"

    await db_session.delete(fetched)
    await db_session.commit()
    assert await db_session.get(UserModel, user.id) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_token_crud(db_session):
    user = UserModel(email="tokenuser@test.com", hashed_password=None)
    db_session.add(user)
    await db_session.commit()

    token = RefreshTokenModel(
        user_id=user.id,
        token="tok123",
        expires_at=datetime(2099, 1, 1, 0, 0, 0)
    )
    db_session.add(token)
    await db_session.commit()

    fetched = await db_session.get(RefreshTokenModel, token.id)
    assert fetched.token == "tok123"
    assert fetched.user_id == user.id

    await db_session.delete(user)
    await db_session.commit()
    assert await db_session.get(RefreshTokenModel, token.id) is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_simulation_crud(db_session):
    user = UserModel(email="simuser@test.com", hashed_password=None)
    db_session.add(user)
    await db_session.commit()

    sim = SimulationModel(
        command="AAPL-L-100% 2021-01-01 2021-01-05",
        tickers=["AAPL"],
        weights={"AAPL": 1.0},
        sides={"AAPL": "L"},
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
        portfolio_value={"2021-01-01": 100000},
        daily_returns={"2021-01-02": 0.01},
        cumulative_returns={"2021-01-02": 0.01},
        cagr=0.1,
        sharpe=1.0,
        max_drawdown=0.0,
        user_id=user.id
    )
    db_session.add(sim)
    await db_session.commit()

    fetched = await db_session.get(SimulationModel, sim.id)
    assert fetched.command.startswith("AAPL")
    assert fetched.user_id == user.id

    await db_session.delete(user)
    await db_session.commit()
    assert await db_session.get(SimulationModel, sim.id) is None

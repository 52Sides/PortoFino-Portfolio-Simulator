import pytest
import pandas as pd
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from core.simulation.data_preparator import DataPreparator
from schemas.simulation import ParsedCommandModel


@pytest.fixture
def parsed_command():
    return ParsedCommandModel(
        tickers=["TSLA", "AAPL"],
        weights=[0.5, 0.5],
        sides=["L", "L"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 3)
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_portfolio_data_fixed(monkeypatch, parsed_command):
    fake_db = AsyncMock()

    monkeypatch.setattr(
        "core.simulation.data_preparator.AssetsRepo.get_portfolio_data_from_db",
        AsyncMock(return_value=pd.DataFrame(columns=["ticker", "date", "close"]))
    )

    fetched_df = pd.DataFrame({
        "ticker": ["TSLA", "AAPL"],
        "date": [date(2021, 1, 1), date(2021, 1, 1)],
        "close": [100, 200],
        "open": [99, 199],
        "high": [101, 201],
        "low": [98, 198],
        "volume": [1000, 2000]
    })
    monkeypatch.setattr(
        "core.simulation.data_preparator.DataPreparator._fetch_missing_data", AsyncMock(return_value=fetched_df)
    )
    monkeypatch.setattr("core.simulation.data_preparator.DataPreparator._save_batch_to_db", AsyncMock())

    result = await DataPreparator.collect_portfolio_data(parsed_command, fake_db)

    expected_cols = ["ticker", "date", "close"]
    assert all(col in result.columns for col in expected_cols)
    assert set(result["ticker"].unique()) == set(parsed_command.tickers)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_identify_missing_ranges(parsed_command):
    db_data = pd.DataFrame({
        "ticker": ["TSLA", "TSLA"],
        "date": pd.to_datetime(["2021-01-01", "2021-01-02"])
    })
    tickers = parsed_command.tickers
    start_date = parsed_command.start_date
    end_date = parsed_command.end_date

    missing = await DataPreparator._identify_missing_ranges(db_data, tickers, start_date, end_date)
    missing_tickers = {t[0] for t in missing}
    assert missing_tickers == {"TSLA", "AAPL"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_identify_missing_ranges_empty_df(parsed_command):
    db_data = pd.DataFrame(columns=["ticker", "date", "close"])
    missing = await DataPreparator._identify_missing_ranges(
        db_data,
        parsed_command.tickers,
        parsed_command.start_date,
        parsed_command.end_date
    )
    tickers_missing = {t[0] for t in missing}
    assert tickers_missing == set(parsed_command.tickers)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_identify_missing_ranges_partial_end(parsed_command):
    tsla_idx = pd.date_range(parsed_command.start_date, periods=2)
    tsla_df = pd.DataFrame({"ticker": ["TSLA"] * 2, "date": tsla_idx})
    db_data = pd.concat([tsla_df, pd.DataFrame(columns=["ticker", "date"])])
    missing = await DataPreparator._identify_missing_ranges(
        db_data,
        parsed_command.tickers,
        parsed_command.start_date,
        parsed_command.end_date
    )
    tsla_missing = [m for m in missing if m[0] == "TSLA"]
    assert tsla_missing[-1][2] == parsed_command.end_date


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_missing_data(monkeypatch):
    async def fake_fetch(ticker, start, end):
        return pd.DataFrame({
            "ticker": [ticker, ticker],
            "date": pd.date_range(start, end),
            "close": [100, 101],
            "open": [99, 100],
            "high": [101, 102],
            "low": [98, 99],
            "volume": [1000, 1000]
        })

    monkeypatch.setattr("core.simulation.data_preparator.fetch_yf_data_async", fake_fetch)
    monkeypatch.setattr("core.simulation.data_preparator.normalize_yfinance_df", lambda df, t, s, e: df)

    tasks = [("TSLA", date(2021, 1, 1), date(2021, 1, 2))]
    result = await DataPreparator._fetch_missing_data(tasks)
    assert "ticker" in result.columns
    assert "open" in result.columns
    assert len(result) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_missing_data_with_exception(monkeypatch):
    async def fail_fetch(ticker, start, end):
        if ticker == "AAPL":
            raise ValueError("fail")
        return pd.DataFrame({"ticker": [ticker], "date": [start], "close": [100]})

    monkeypatch.setattr("core.simulation.data_preparator.fetch_yf_data_async", fail_fetch)
    monkeypatch.setattr(
        "core.simulation.data_preparator.normalize_yfinance_df",
        lambda df, ticker, start, end: pd.DataFrame() if isinstance(df, Exception) else df.assign(ticker=ticker)
    )

    tasks = [
        ("TSLA", date(2021, 1, 1), date(2021, 1, 1)),
        ("AAPL", date(2021, 1, 1), date(2021, 1, 1))
    ]

    result = await DataPreparator._fetch_missing_data(tasks)

    tsla_df = result[result["ticker"] == "TSLA"]
    assert not tsla_df.empty

    aapl_df = result[result.get("ticker", "") == "AAPL"]
    assert aapl_df.empty or aapl_df.shape[0] == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_batch_to_db_fixed(monkeypatch):
    df = pd.DataFrame({
        "ticker": ["TSLA"],
        "date": [pd.Timestamp("2021-01-01")],
        "open": [None],
        "high": [2],
        "low": [0],
        "close": [1.5],
        "volume": [100],
    })
    fake_db = AsyncMock()

    fake_stmt = MagicMock()
    fake_values = MagicMock()
    fake_values.on_conflict_do_nothing.return_value = fake_stmt

    class FakeInsert:
        def values(self, x):
            return fake_values

    monkeypatch.setattr("core.simulation.data_preparator.insert", lambda x: FakeInsert())
    monkeypatch.setattr("core.simulation.data_preparator.AssetsModel", object)

    await DataPreparator._save_batch_to_db(fake_db, df)

    fake_db.execute.assert_awaited_once_with(fake_stmt)
    fake_db.commit.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_batch_to_db_no_data(monkeypatch):
    fake_db = AsyncMock()
    await DataPreparator._save_batch_to_db(fake_db, pd.DataFrame())
    fake_db.execute.assert_not_awaited()
    fake_db.commit.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_db_and_fetched_variants():
    out = await DataPreparator._merge_db_and_fetched(pd.DataFrame(), pd.DataFrame())
    assert out.empty

    new_data = pd.DataFrame({
        "ticker": ["TSLA"],
        "date": [pd.Timestamp("2021-01-01")],
        "close": [100]
    })
    out = await DataPreparator._merge_db_and_fetched(pd.DataFrame(), new_data)
    assert "ticker" in out.columns
    assert "close" in out.columns
    assert len(out) == 1

    db_data = pd.DataFrame({
        "ticker": ["AAPL"],
        "date": [pd.Timestamp("2021-01-01")],
        "close": [200]
    })
    out = await DataPreparator._merge_db_and_fetched(db_data, pd.DataFrame())
    assert len(out) == 1

    db_data2 = pd.DataFrame({
        "ticker": ["TSLA"],
        "date": [pd.Timestamp("2021-01-01")],
        "close": [99]
    })
    new_data2 = pd.DataFrame({
        "ticker": ["TSLA"],
        "date": [pd.Timestamp("2021-01-01")],
        "close": [100]
    })
    out = await DataPreparator._merge_db_and_fetched(db_data2, new_data2)
    assert out.iloc[0]["close"] == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_missing_data_empty_and_exception(monkeypatch):
    out = await DataPreparator._fetch_missing_data([])
    assert out.empty

    async def fail_fetch(*args, **kwargs):
        raise ValueError("fail")

    monkeypatch.setattr("core.simulation.data_preparator.fetch_yf_data_async", fail_fetch)
    monkeypatch.setattr(
        "core.simulation.data_preparator.normalize_yfinance_df",
        lambda df, t, s, e: pd.DataFrame(columns=["ticker", "date", "open", "high", "low", "close", "volume"])
    )

    tasks = [("TSLA", date(2021, 1, 1), date(2021, 1, 2))]
    out = await DataPreparator._fetch_missing_data(tasks)
    assert all(col in out.columns for col in ["ticker", "date", "open", "high", "low", "close", "volume"])


@pytest.mark.unit
@pytest.mark.asyncio
async def test_identify_missing_ranges_middle_gap():
    tickers = ["TSLA"]
    db_data = pd.DataFrame({
        "ticker": ["TSLA", "TSLA"],
        "date": ["2021-01-01", "2021-01-04"],
        "open": [100, 102],
        "high": [101, 103],
        "low": [99, 101],
        "close": [100.5, 102.5],
        "volume": [1000, 1200]
    })
    db_data["date"] = pd.to_datetime(db_data["date"]).dt.date
    db_data = db_data.reset_index(drop=True)
    date_start = date(2021, 1, 1)
    date_end = date(2021, 1, 4)
    missing = await DataPreparator._identify_missing_ranges(db_data, tickers, date_start, date_end)

    assert missing == [("TSLA", date(2021, 1, 2), date(2021, 1, 3))]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_batch_to_db_empty_and_exception(monkeypatch):
    fake_db = AsyncMock()

    await DataPreparator._save_batch_to_db(fake_db, pd.DataFrame())
    fake_db.execute.assert_not_awaited()

    df = pd.DataFrame({
        "ticker": ["TSLA"],
        "date": [pd.Timestamp("2021-01-01")],
        "open": [1],
        "high": [2],
        "low": [0],
        "close": [1.5],
        "volume": [100]
    })

    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()

    class FakeInsert:
        def values(self, x):
            return self

        def on_conflict_do_nothing(self, **kwargs):
            return self

    import core.simulation.data_preparator as dp
    monkeypatch.setattr(dp, "insert", lambda x: FakeInsert())
    monkeypatch.setattr(dp, "AssetsModel", object)

    fake_db.execute.side_effect = Exception("DB fail")

    with pytest.raises(Exception):
        await DataPreparator._save_batch_to_db(fake_db, df)

    fake_db.rollback.assert_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_portfolio_data_full(parsed_command, monkeypatch):
    fake_db = AsyncMock()

    monkeypatch.setattr(
        "core.simulation.data_preparator.AssetsRepo.get_portfolio_data_from_db",
        AsyncMock(return_value=pd.DataFrame(columns=["ticker", "date", "close", "open", "high", "low", "volume"]))
    )
    monkeypatch.setattr(
        "core.simulation.data_preparator.DataPreparator._fetch_missing_data",
        AsyncMock(return_value=pd.DataFrame({
            "ticker": ["TSLA", "AAPL"],
            "date": [date(2021, 1, 1), date(2021, 1, 1)],
            "close": [100, 200],
            "open": [99, 199],
            "high": [101, 201],
            "low": [98, 198],
            "volume": [1000, 2000]
        }))
    )
    monkeypatch.setattr("core.simulation.data_preparator.DataPreparator._save_batch_to_db", AsyncMock())

    result = await DataPreparator.collect_portfolio_data(parsed_command, fake_db)

    for col in ["ticker", "date", "close"]:
        assert col in result.columns

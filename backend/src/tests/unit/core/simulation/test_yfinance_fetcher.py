from datetime import date
import pandas as pd
import pytest

import yfinance as yf

from core.simulation.yfinance_fetcher import fetch_yf_data_async, normalize_yfinance_df, COLUMNS_STD


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_price_series_returns_dataframe(monkeypatch):
    """Ensure the function returns a DataFrame with expected columns."""

    def fake_download(*args, **kwargs):
        dates = pd.date_range("2024-01-01", periods=3)
        return pd.DataFrame({
            "Open": [1, 2, 3],
            "High": [2, 3, 4],
            "Low": [0.5, 1.5, 2.5],
            "Close": [10, 20, 30],
            "Volume": [100, 200, 300]
        }, index=dates)

    monkeypatch.setattr(yf, "download", fake_download)

    result = await fetch_yf_data_async("AAPL", pd.to_datetime("2024-01-01"), pd.to_datetime("2024-01-03"))

    assert isinstance(result, pd.DataFrame)

    expected_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in expected_cols:
        assert col in result.columns
    assert result["Close"].to_list() == [10, 20, 30]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_price_series_empty_data(monkeypatch):
    """Check behavior when the fetched data is empty."""
    monkeypatch.setattr(yf, "download", lambda *a, **k: pd.DataFrame())

    result = await fetch_yf_data_async("AAPL", pd.to_datetime("2024-01-01"), pd.to_datetime("2024-01-03"))
    assert result.empty


@pytest.mark.unit
@pytest.mark.asyncio
def test_normalize_yf_df_empty():
    """Return a valid DataFrame when input is empty or None."""
    ticker = "AAPL"
    date_start = date(2024, 1, 1)
    date_end = date(2024, 1, 5)

    result_none = normalize_yfinance_df(None, ticker, date_start, date_end)
    assert list(result_none.columns) == COLUMNS_STD
    assert result_none["ticker"].iloc[0] == ticker
    assert "date" in result_none.columns

    empty_df = pd.DataFrame()
    result_empty = normalize_yfinance_df(empty_df, ticker, date_start, date_end)
    assert list(result_empty.columns) == COLUMNS_STD
    assert result_empty["ticker"].iloc[0] == ticker
    assert not result_empty.empty


@pytest.mark.unit
def test_normalize_yf_df_with_data():
    """Check correct transformation of a DataFrame with actual data."""
    ticker = "MSFT"
    data = {
        "Open": [100, 110],
        "High": [120, 130],
        "Low": [90, 100],
        "Close": [115, 125],
        "Volume": [1000, 2000],
    }
    df = pd.DataFrame(data, index=pd.to_datetime(["2024-01-02", "2024-01-03"]))

    normalized = normalize_yfinance_df(df, ticker, date(2024, 1, 1), date(2024, 1, 3))

    assert list(normalized.columns) == COLUMNS_STD
    assert normalized["ticker"].iloc[0] == ticker
    assert "date" in normalized.columns

    row_20240102 = normalized[normalized['date'] == date(2024, 1, 2)].iloc[0]
    assert row_20240102["open"] == 100
    assert row_20240102["high"] == 120
    assert row_20240102["low"] == 90
    assert row_20240102["close"] == 115
    assert row_20240102["volume"] == 1000

    row_20240103 = normalized[normalized['date'] == date(2024, 1, 3)].iloc[0]
    assert row_20240103["open"] == 110
    assert row_20240103["high"] == 130
    assert row_20240103["low"] == 100
    assert row_20240103["close"] == 125
    assert row_20240103["volume"] == 2000

    row_20240101 = normalized[normalized['date'] == date(2024, 1, 1)].iloc[0]
    assert pd.isna(row_20240101["open"])
    assert pd.isna(row_20240101["high"])
    assert pd.isna(row_20240101["low"])
    assert pd.isna(row_20240101["close"])
    assert pd.isna(row_20240101["volume"])

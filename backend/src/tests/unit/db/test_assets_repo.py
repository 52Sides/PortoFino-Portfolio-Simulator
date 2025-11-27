import pytest
import pandas as pd
from unittest.mock import MagicMock

from db.repositories.assets_repo import AssetsRepo


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_price_series_from_db_no_rows(mock_db):
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    result = await AssetsRepo.get_portfolio_data_from_db(
        mock_db, ["AAPL"], pd.to_datetime("2024-01-01").date(), pd.to_datetime("2024-01-10").date()
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == ["ticker", "date", "open", "high", "low", "close", "volume"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_price_series_from_db_with_rows(mock_db):
    rows = [
        {
            "ticker": "AAPL",
            "date": pd.to_datetime("2024-01-02").date(),
            "open": None,
            "high": None,
            "low": None,
            "close": 150.5,
            "volume": None
        },
        {
            "ticker": "AAPL",
            "date": pd.to_datetime("2024-01-03").date(),
            "open": None,
            "high": None,
            "low": None,
            "close": 152.1,
            "volume": None
        },
    ]

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_db.execute.return_value = mock_result

    result = await AssetsRepo.get_portfolio_data_from_db(
        mock_db, ["AAPL"], pd.to_datetime("2024-01-01").date(), pd.to_datetime("2024-01-10").date()
    )

    assert isinstance(result, pd.DataFrame)
    assert list(result["close"]) == [150.5, 152.1]
    assert list(result.columns) == ["ticker", "date", "open", "high", "low", "close", "volume"]

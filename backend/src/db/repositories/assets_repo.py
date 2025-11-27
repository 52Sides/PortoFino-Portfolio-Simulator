from datetime import date
from typing import List
import pandas as pd

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assets_model import AssetsModel


class AssetsRepo:

    @staticmethod
    async def get_portfolio_data_from_db(
        db: AsyncSession,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Returns DataFrame with columns. Example:
            ticker  date         open    high    low     close   volume
        0   AAPL    2024-01-02   189.55  190.47  187.16  189.10  51234.0
        Rows filtered by tickers and date range [start_date, end_date] inclusive,
        ordered by ticker then date. Returns empty DataFrame with correct columns if no rows.
        """

        cols = ["ticker", "date", "open", "high", "low", "close", "volume"]

        if not tickers:
            return pd.DataFrame(columns=cols)

        stmt = (
            select(
                AssetsModel.ticker,
                AssetsModel.date,
                AssetsModel.open,
                AssetsModel.high,
                AssetsModel.low,
                AssetsModel.close,
                AssetsModel.volume,
            )
            .where(
                AssetsModel.ticker.in_(tickers),
                AssetsModel.date >= start_date,
                AssetsModel.date <= end_date,
            )
            .order_by(AssetsModel.ticker, AssetsModel.date)
        )

        res = await db.execute(stmt)
        rows = res.mappings().all()

        if not rows:
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(rows)
        df = df[cols]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.reset_index(drop=True)

        return df

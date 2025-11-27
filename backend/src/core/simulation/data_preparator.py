import asyncio
import logging
from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from core.simulation.yfinance_fetcher import normalize_yfinance_df, fetch_yf_data_async
from db.models import AssetsModel
from db.repositories.assets_repo import AssetsRepo
from schemas.simulation import ParsedCommandModel

logger = logging.getLogger(__name__)


class DataPreparator:
    """Async price data aggregator."""

    @staticmethod
    async def collect_portfolio_data(parsed_command: ParsedCommandModel, db: AsyncSession) -> pd.DataFrame:
        tickers = parsed_command.tickers
        start_date = parsed_command.start_date
        end_date = parsed_command.end_date

        logger.info(f"[DataPreparator] Collecting data: tickers={tickers}, {start_date}, {end_date}")

        db_data = await AssetsRepo.get_portfolio_data_from_db(db, tickers, start_date, end_date)
        logger.debug("[DataPreparator] DB data rows: %s", len(db_data))

        missing_tasks = await DataPreparator._identify_missing_ranges(db_data, tickers, start_date, end_date)
        logger.info("[DataPreparator] Missing ranges: %s", missing_tasks)

        new_data = await DataPreparator._fetch_missing_data(missing_tasks)
        logger.info("[DataPreparator] Fetched new data rows: %s", 0 if new_data is None else len(new_data))

        await DataPreparator._save_batch_to_db(db, new_data)
        logger.info("[DataPreparator] DB updated")

        combined_data = await DataPreparator._merge_db_and_fetched(db_data, new_data)
        logger.info("[DataPreparator] Combined data rows: %s", len(combined_data))

        return combined_data

    @staticmethod
    async def _merge_db_and_fetched(db_data: pd.DataFrame, new_data: pd.DataFrame) -> pd.DataFrame:
        """Merge DB and fetched data, preferring fetched values."""

        cols = ["ticker", "date", "close"]

        if not db_data.empty:
            db_data["date"] = pd.to_datetime(db_data["date"]).dt.date
        if not new_data.empty:
            new_data["date"] = pd.to_datetime(new_data["date"]).dt.date

        if db_data.empty and new_data.empty:
            return pd.DataFrame(columns=cols)

        if db_data.empty or new_data.empty:
            out = new_data.copy() if db_data.empty else db_data.copy()
            return out[cols].sort_values(["ticker", "date"]).reset_index(drop=True)

        merged = pd.concat([db_data[cols], new_data[cols]], ignore_index=True)
        merged = merged.drop_duplicates(subset=["ticker", "date"], keep="last")
        return merged.sort_values(["ticker", "date"]).reset_index(drop=True)

    @staticmethod
    async def _identify_missing_ranges(
        db_data: pd.DataFrame,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> List[Tuple[str, date, date]]:
        """Find continuous missing date ranges for each ticker."""

        full_calendar = [d.date() for d in pd.date_range(start=start_date, end=end_date, freq="D")]
        missing_ranges: List[Tuple[str, date, date]] = []

        for ticker in tickers:
            ticker_df = db_data[db_data["ticker"] == ticker]

            if ticker_df.empty:
                logger.debug("Missing full range for %s", ticker)
                missing_ranges.append((ticker, start_date, end_date))
                continue

            available_dates = set(ticker_df["date"])
            current_start = None

            for d in full_calendar:
                if d not in available_dates:
                    if current_start is None:
                        current_start = d
                else:
                    if current_start is not None:
                        missing_ranges.append((ticker, current_start, d - timedelta(days=1)))
                        current_start = None

            if current_start is not None:
                missing_ranges.append((ticker, current_start, end_date))

        return missing_ranges

    @staticmethod
    async def _fetch_missing_data(missing_tasks: List[Tuple[str, date, date]]) -> pd.DataFrame:
        """Fetch and normalize missing ranges from yfinance."""

        if not missing_tasks:
            return pd.DataFrame(columns=["ticker", "date", "open", "high", "low", "close", "volume"])

        coros = [
            fetch_yf_data_async(ticker, start_date, end_date)
            for ticker, start_date, end_date in missing_tasks
        ]

        fetched_list = await asyncio.gather(*coros, return_exceptions=True)
        frames = []

        for (ticker, start_date, end_date), df in zip(missing_tasks, fetched_list):
            if isinstance(df, Exception) or df is None or df.empty:
                logger.warning("Fetch error or empty for %s", ticker)
                df = pd.DataFrame()

            normalized = normalize_yfinance_df(df, ticker, start_date, end_date)
            frames.append(normalized)

        if not frames:
            return pd.DataFrame(columns=["ticker", "date", "open", "high", "low", "close", "volume"])

        out = pd.concat(frames, ignore_index=True)
        return out.sort_values(["ticker", "date"]).reset_index(drop=True)

    @staticmethod
    async def _save_batch_to_db(db: AsyncSession, fetched_results: pd.DataFrame, batch_size: int = 1000):
        """Insert fetched data into DB in batches."""

        if fetched_results is None or fetched_results.empty:
            logger.debug("No fetched data to save")
            return

        def _clean(v):
            return None if pd.isna(v) else float(v)

        batch_rows = [
            {
                "ticker": row["ticker"],
                "date": pd.to_datetime(row["date"]).date(),
                "open": _clean(row["open"]),
                "high": _clean(row["high"]),
                "low": _clean(row["low"]),
                "close": _clean(row["close"]),
                "volume": _clean(row["volume"]),
            }
            for _, row in fetched_results.iterrows()
        ]

        if not batch_rows:
            logger.debug("No rows after cleaning")
            return

        logger.info("Saving %s rows to DB", len(batch_rows))

        for i in range(0, len(batch_rows), batch_size):
            sub_batch = batch_rows[i:i + batch_size]
            stmt = (
                insert(AssetsModel)
                .values(sub_batch)
                .on_conflict_do_nothing(index_elements=["ticker", "date"])
            )
            try:
                await db.execute(stmt)
                await db.commit()
                logger.debug("Committed batch %s", i // batch_size + 1)
            except Exception as e:
                logger.error("DB batch error %s: %s", i // batch_size + 1, e)
                await db.rollback()
                raise

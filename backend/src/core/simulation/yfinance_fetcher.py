from __future__ import annotations

import asyncio
import pandas as pd
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf

MAX_WORKERS = 8
YF_COLUMNS_RAW = ["Open", "High", "Low", "Close", "Volume"]
COLUMNS_STD = ["ticker", "date", "open", "high", "low", "close", "volume"]

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


# --- Helpers ---
def _empty_yf_raw() -> pd.DataFrame:
    """Return an empty DataFrame matching raw yfinance schema."""
    return pd.DataFrame(columns=YF_COLUMNS_RAW)


def _empty_normalized(ticker: str, date_start: date, date_end: date) -> pd.DataFrame:
    """Return an empty calendar-aligned normalized price frame."""
    full_index = pd.date_range(start=date_start, end=date_end, freq="D")

    df = pd.DataFrame(index=full_index, columns=COLUMNS_STD[2:], dtype="float64")
    df = df.reset_index().rename(columns={"index": "date"})
    df["ticker"] = ticker
    df["date"] = df["date"].dt.date

    return df[COLUMNS_STD]


# --- Fetch data via yfinance ---
def _fetch_yf_data_sync(ticker: str, date_start: date, date_end: date) -> pd.DataFrame:
    """Fetch OHLCV data synchronously via yfinance."""
    try:
        df = yf.download(
            ticker,
            start=date_start.strftime("%Y-%m-%d"),
            end=date_end.strftime("%Y-%m-%d"),
            progress=False,
            auto_adjust=False,
        )
        if df is None or df.empty:
            return _empty_yf_raw()

        return df
    except Exception as e:
        print(f"[YF ERROR] ticker={ticker}, range={date_start}..{date_end}: {e}")
        return _empty_yf_raw()


async def fetch_yf_data_async(ticker: str, date_start: date, date_end: date) -> pd.DataFrame:
    """Async wrapper for yfinance fetch using a thread pool and end_date+1 logic."""
    loop = asyncio.get_running_loop()

    df = await loop.run_in_executor(
        _executor, _fetch_yf_data_sync,
        ticker,
        date_start,
        date_end + timedelta(days=1),
    )

    if df is None or df.empty:
        return _empty_yf_raw()

    return df


# --- Normalization ---
def normalize_yfinance_df(df: pd.DataFrame, ticker: str, date_start: date, date_end: date) -> pd.DataFrame:
    """
    Normalize yfinance output into a full daily calendar with fixed columns:
    ticker | date | open | high | low | close | volume
    """
    full_index = pd.date_range(start=date_start, end=date_end, freq="D")

    df_full = pd.DataFrame(
        index=full_index,
        columns=["open", "high", "low", "close", "volume"],
        dtype="float64"
    )

    if df is not None and not df.empty:
        df_copy = df.copy()
        df_copy.index = pd.to_datetime(df_copy.index).normalize()
        if isinstance(df_copy.columns, pd.MultiIndex):
            df_copy.columns = [c[0] for c in df_copy.columns]

        rename_map = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df_copy = df_copy.rename(columns=rename_map)
        df_copy = df_copy[[col for col in ["open", "high", "low", "close", "volume"]]]
        df_copy = df_copy.loc[pd.Index(df_copy.index).intersection(full_index)]
        df_full.loc[df_copy.index] = df_copy

    # Финальная упаковка
    out = df_full.reset_index().rename(columns={"index": "date"})
    out["ticker"] = ticker
    out["date"] = out["date"].dt.date

    return out[COLUMNS_STD]

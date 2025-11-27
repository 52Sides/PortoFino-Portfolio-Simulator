from __future__ import annotations

import math
import pandas as pd

from schemas.simulation import ParsedCommandModel
from db.models import SimulationModel


class PortfolioSimulator:
    """Simulates portfolio value and performance metrics over time."""

    def __init__(
        self,
        command_str: str,
        command_parsed: ParsedCommandModel,
        combined_df: pd.DataFrame,
        user_id: int,
        budget: float = 100_000.0,
        risk_free_rate: float = 0.0,
    ):
        if not isinstance(command_parsed, ParsedCommandModel):
            raise TypeError("command_parsed must be ParsedCommandModel")
        if not isinstance(combined_df, pd.DataFrame):
            raise TypeError("combined_df must be pd.DataFrame")
        if combined_df.empty or "date" not in combined_df.columns:
            raise ValueError("combined_df must contain 'date' column")

        self.command_str = command_str
        self.command_parsed = command_parsed

        df = combined_df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        self.pd_data = df.sort_values(["ticker", "date"])

        self.user_id = user_id
        self.budget = budget
        self.risk_free_rate = risk_free_rate

    def _build_portfolio_series(self) -> pd.Series:
        """Construct portfolio value time series from weighted long/short positions."""

        frames = []
        weights_sum = 0.0

        weights = dict(zip(self.command_parsed.tickers, self.command_parsed.weights))
        sides = dict(zip(self.command_parsed.tickers, self.command_parsed.sides))

        for ticker in self.command_parsed.tickers:
            weight = weights.get(ticker, 0.0)
            side = sides.get(ticker, "L").upper()

            df_ticker = self.pd_data[self.pd_data["ticker"] == ticker]
            if df_ticker.empty:
                continue

            s = df_ticker.set_index("date")["close"].astype(float)
            if s.isna().all():
                continue

            first_valid = s.first_valid_index()
            if first_valid is None:
                continue

            s = s.loc[first_valid:].sort_index()
            s = s.ffill()

            initial_price = s.iloc[0]
            if initial_price == 0 or math.isnan(initial_price):
                continue

            value = (s / initial_price) * (self.budget * weight)

            if side == "S":
                value = self.budget * weight * 2 - value

            frames.append(value)
            weights_sum += weight

        if not frames:
            raise ValueError("No valid ticker data available for simulation")

        combined = (
            pd.concat(frames, axis=1, join="outer")
            .sort_index()
            .ffill()
            .fillna(0)
        )

        cash_weight = max(1.0 - weights_sum, 0.0)
        if cash_weight > 0:
            combined["CASH"] = self.budget * cash_weight

        pv = combined.sum(axis=1)
        pv.name = "portfolio_value"

        return pv

    @staticmethod
    def _daily_returns(portfolio_value: pd.Series) -> pd.Series:
        """Compute daily percentage returns."""
        return portfolio_value.pct_change().dropna()

    @staticmethod
    def _cumulative_returns(rets: pd.Series) -> pd.Series:
        """Compute cumulative returns from daily returns."""
        return (1 + rets).cumprod() - 1

    @staticmethod
    def _cagr(portfolio_value: pd.Series) -> float:
        """Compute CAGR from start to end of portfolio value series."""
        start = float(portfolio_value.iloc[0])
        end = float(portfolio_value.iloc[-1])

        if start == 0 or end == 0 or math.isnan(start) or math.isnan(end):
            return 0.0

        ratio = abs(end / start) or 1e-12
        days = (portfolio_value.index[-1] - portfolio_value.index[0]).days
        years = max(days / 365.25, 1 / 365.25)

        return ratio ** (1 / years) - 1

    def _sharpe_ratio(self, rets: pd.Series) -> float:
        """Compute annualized Sharpe ratio."""
        excess = rets - (self.risk_free_rate / 252)
        std = excess.std()
        if std == 0:
            return float("nan")
        return (excess.mean() * 252) / (std * math.sqrt(252))

    @staticmethod
    def _max_drawdown(cum: pd.Series) -> float:
        """Compute max drawdown from cumulative returns."""
        running_max = (1 + cum).cummax()
        dd = (1 + cum) / running_max - 1
        return abs(dd.min())

    @staticmethod
    def _safe_float(x):
        """Convert to float and sanitize NaN/inf."""
        try:
            v = float(x)
            if math.isnan(v) or math.isinf(v):
                return None

            return v

        except Exception:
            return None

    def run(self) -> SimulationModel:
        """Run full simulation and return results model."""
        portfolio_value = self._build_portfolio_series()
        daily_returns = self._daily_returns(portfolio_value)

        portfolio_value_iso = {d.strftime("%Y-%m-%d"): float(v) for d, v in portfolio_value.items()}
        cagr = self._safe_float(self._cagr(portfolio_value))

        if daily_returns.empty:
            return SimulationModel(
                user_id=self.user_id,
                command=self.command_str,
                start_date=self.command_parsed.start_date,
                end_date=self.command_parsed.end_date,
                tickers=self.command_parsed.tickers,
                weights=self.command_parsed.weights,
                sides=self.command_parsed.sides,
                portfolio_value=portfolio_value_iso,
                daily_returns={},
                cumulative_returns={},
                cagr=cagr,
                sharpe=None,
                max_drawdown=None,
            )

        cum = self._cumulative_returns(daily_returns)

        daily_returns_iso = {d.strftime("%Y-%m-%d"): float(v) for d, v in daily_returns.items()}
        cumulative_returns_iso = {d.strftime("%Y-%m-%d"): float(v) for d, v in cum.items()}

        sharpe = self._safe_float(self._sharpe_ratio(daily_returns))
        max_dd = self._safe_float(self._max_drawdown(cum))

        return SimulationModel(
            user_id=self.user_id,
            command=self.command_str,
            start_date=self.command_parsed.start_date,
            end_date=self.command_parsed.end_date,
            tickers=self.command_parsed.tickers,
            weights=self.command_parsed.weights,
            sides=self.command_parsed.sides,
            portfolio_value=portfolio_value_iso,
            daily_returns=daily_returns_iso,
            cumulative_returns=cumulative_returns_iso,
            cagr=cagr,
            sharpe=sharpe,
            max_drawdown=max_dd,
        )

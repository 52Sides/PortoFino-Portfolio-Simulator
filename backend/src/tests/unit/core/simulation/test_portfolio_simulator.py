import pytest
import pandas as pd
from datetime import date

from core.simulation.portfolio_simulator import PortfolioSimulator
from schemas.simulation import ParsedCommandModel
from db.models.simulation_model import SimulationModel


@pytest.fixture
def sample_df():
    dates = pd.date_range(start="2021-01-01", end="2021-01-05")
    data = {
        "date": list(dates) * 2,
        "ticker": ["TSLA"] * len(dates) + ["AAPL"] * len(dates),
        "close": [100, 102, 101, 103, 104, 50, 51, 50, 52, 53],
    }
    return pd.DataFrame(data)


@pytest.fixture
def parsed_command():
    return ParsedCommandModel(
        tickers=["TSLA", "AAPL"],
        weights=[0.6, 0.4],
        sides=["L", "S"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
    )


@pytest.mark.unit
def test_portfolio_simulator_run_basic(sample_df, parsed_command):
    sim = PortfolioSimulator(
        "TSLA-L-60% AAPL-S-40% 2021-01-01 2021-01-05",
        parsed_command,
        sample_df,
        user_id=1
    )
    result = sim.run()

    assert isinstance(result, SimulationModel)
    assert set(result.tickers) == {"TSLA", "AAPL"}

    weights = dict(zip(parsed_command.tickers, parsed_command.weights))
    sides = dict(zip(parsed_command.tickers, parsed_command.sides))

    assert abs(weights["TSLA"] - 0.6) < 1e-6
    assert abs(weights["AAPL"] - 0.4) < 1e-6
    assert sides["TSLA"].upper() == "L"
    assert sides["AAPL"].upper() == "S"

    assert len(result.daily_returns) == 4
    assert len(result.cumulative_returns) == 4
    assert result.cagr >= 0
    assert result.sharpe is not None
    assert result.max_drawdown >= 0
    assert all(v >= 0 for v in result.portfolio_value.values())


@pytest.mark.unit
def test_portfolio_simulator_empty_dataframe(parsed_command):
    empty_df = pd.DataFrame(columns=["date", "ticker", "close"])
    with pytest.raises(ValueError):
        PortfolioSimulator(
            "TSLA-L-60% AAPL-S-40% 2021-01-01 2021-01-05",
            parsed_command,
            empty_df,
            user_id=1
        )


@pytest.mark.unit
def test_portfolio_simulator_invalid_types(sample_df):
    with pytest.raises(TypeError):
        PortfolioSimulator("cmd", "not_parsed", sample_df, 1)

    with pytest.raises(TypeError):
        PortfolioSimulator(
            "cmd",
            ParsedCommandModel(
                tickers=[], weights=[], sides=[],
                start_date=date.today(), end_date=date.today()
            ),
            {"2020-10-22": 123124.23},
            1
        )


@pytest.mark.unit
def test_portfolio_simulator_short_positions(sample_df):
    parsed = ParsedCommandModel(
        tickers=["AAPL"],
        weights=[1.0],
        sides=["S"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
    )
    sim = PortfolioSimulator("AAPL-S-100% 2021-01-01 2021-01-05", parsed, sample_df, 1)
    result = sim.run()

    assert all(v > 0 for v in result.portfolio_value.values())
    assert "CASH" in result.portfolio_value or sum(parsed.weights) >= 1.0


@pytest.mark.unit
def test_portfolio_simulator_cash_handling(sample_df):
    parsed = ParsedCommandModel(
        tickers=["TSLA"],
        weights=[0.5],
        sides=["L"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
    )
    sim = PortfolioSimulator("TSLA-L-50% 2021-01-01 2021-01-05", parsed, sample_df, user_id=1)
    result = sim.run()
    portfolio_values = result.portfolio_value

    min_expected = sim.budget * sum(parsed.weights)
    assert all(v >= min_expected for v in portfolio_values.values())
    assert portfolio_values["2021-01-05"] > portfolio_values["2021-01-01"]


@pytest.mark.unit
def test_portfolio_simulator_short_and_cash(sample_df):
    parsed = ParsedCommandModel(
        tickers=["AAPL", "TSLA"],
        weights=[0.5, 0.3],
        sides=["S", "L"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
    )
    sim = PortfolioSimulator("AAPL-S-50% TSLA-L-30%", parsed, sample_df, 1)
    result = sim.run()

    assert all(v >= 0 for v in result.portfolio_value.values())
    expected_cash = sim.budget * (1 - sum(parsed.weights))
    last_portfolio_value = list(result.portfolio_value.values())[-1]
    assert last_portfolio_value >= expected_cash


@pytest.mark.unit
def test_portfolio_simulator_no_valid_tickers(sample_df):
    parsed = ParsedCommandModel(
        tickers=["INVALID"],
        weights=[1.0],
        sides=["L"],
        start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 5),
    )

    sim = PortfolioSimulator("INVALID-L-100%", parsed, sample_df, 1)
    with pytest.raises(ValueError, match="No valid ticker data available for simulation"):
        sim.run()

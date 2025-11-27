import pytest
from datetime import date
from pathlib import Path

from core.report import xls_generator


@pytest.fixture
def mock_simulation():
    return {
        "simulation_id": 123,
        "user_id": 42,
        "command": "TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01",
        "start_date": date(2020, 1, 1),
        "end_date": date(2021, 1, 1),
        "cagr": 0.15,
        "sharpe": 1.2,
        "max_drawdown": -0.1,
        "tickers": ["TSLA", "AAPL"],
        "weights": [0.5, 0.5],
        "sides": ["L", "S"],
        "portfolio_value": [{"date": date(2020, 1, 1), "value": 1000}],
        "daily_returns": [{"date": date(2020, 1, 1), "value": 0.01}],
        "cumulative_returns": [{"date": date(2020, 1, 1), "value": 0.01}],
    }


@pytest.mark.unit
def test_generate_xlsx_report(tmp_path, mock_simulation):
    """Verify that generate_xlsx_report produces a valid XLSX file from simulation data."""
    task_id = "TEST123"
    xls_generator.REPORTS_DIR = tmp_path

    output_path = xls_generator.generate_xls_report(task_id, mock_simulation)

    path = Path(output_path)
    assert path.exists(), "Report file must exist"
    assert path.suffix == ".xls", "Report must be in XLS format"
    assert path.stat().st_size > 0, "Report file must not be empty"

import logging
import tempfile
from pathlib import Path

from openpyxl import Workbook

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(tempfile.gettempdir()) / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_xls_report(task_id: str, sim_data: dict) -> str:
    """Generates an XLSX report from simulation data. CPU-bound part, called in Celery."""

    try:
        logger.info(f"[report:{task_id}] Generating XLS report...")

        wb = Workbook()
        ws = wb.active
        ws.title = "Simulation Report"

        # Heading
        ws.append(["Simulation ID", sim_data.get("simulation_id")])
        ws.append(["User ID", sim_data.get("user_id")])
        ws.append(["Command", sim_data.get("command")])
        ws.append(["Date Range", f"{sim_data.get('start_date')} → {sim_data.get('end_date')}"])
        ws.append([])

        # Metrics
        ws.append(["Metrics"])
        ws.append(["CAGR", sim_data.get("cagr")])
        ws.append(["Sharpe", sim_data.get("sharpe")])
        ws.append(["Max Drawdown", sim_data.get("max_drawdown")])
        ws.append([])

        # Portfolio
        ws.append(["Portfolio Summary"])
        tickers = sim_data.get("tickers", [])
        weights = sim_data.get("weights", [])
        sides = sim_data.get("sides", [])
        ws.append(["Ticker", "Weight", "Side"])
        for t, w, s in zip(tickers, weights, sides):
            ws.append([t, w, s])
        ws.append([])

        # Portfolio history
        ws.append(["Portfolio Value"])
        portfolio = sim_data.get("portfolio_value", [])
        ws.append(["Date", "Value"])
        for entry in portfolio:
            if isinstance(entry, dict):
                ws.append([entry.get("date"), entry.get("value") or entry.get("portfolio_value")])
        ws.append([])

        # Profitability
        ws.append(["Daily Returns"])
        ws.append(["Date", "Return"])
        for entry in sim_data.get("daily_returns", []):
            ws.append([entry.get("date"), entry.get("value")])
        ws.append([])

        ws.append(["Cumulative Returns"])
        ws.append(["Date", "Cumulative Return"])
        for entry in sim_data.get("cumulative_returns", []):
            ws.append([entry.get("date"), entry.get("value")])

        # Save the file
        sim_id = sim_data.get("simulation_id")
        file_path = REPORTS_DIR / f"report_{sim_id}.xls"
        wb.save(file_path)
        logger.info(f"[report:{task_id}] XLS saved at {file_path}")

        return str(file_path)

    except Exception as e:
        logger.exception(f"[report:{task_id}] Failed to generate XLS", exc_info=e)
        raise

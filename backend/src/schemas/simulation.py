from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ParsedCommandModel(BaseModel):
    tickers: List[str]      # ["AAPL", "TSLA"]
    weights: List[float]    # ["0.5", "0.5"]
    sides: List[str]        # ["L", "S"]
    start_date: date
    end_date: date


class SimulateRequest(BaseModel):
    command: str = Field(
        ..., description="Simulation command string, example: 'TSLA-L-50% AAPL-S-50% 2020-01-01 2021-01-01'"
    )


class SimulateResponse(BaseModel):
    task_id: str
    status: str = "queued"


class SimulateResponseWS(BaseModel):
    cagr: Optional[float] = None
    sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    portfolio_value: Dict[str, float]

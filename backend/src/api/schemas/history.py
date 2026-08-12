from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class SimHistoryMetrics(BaseModel):
    id: int
    user_id: int
    command: str
    cagr: float | None
    sharpe: float | None
    max_drawdown: float | None
    created_at: datetime


class SimHistoryDetail(SimHistoryMetrics):
    portfolio_value: Dict[str, float]


class PaginatedSimHistoryList(BaseModel):
    total: int
    page: int
    page_size: int
    root: List[SimHistoryMetrics]

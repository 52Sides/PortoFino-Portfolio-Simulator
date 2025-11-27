from sqlalchemy import Column, Integer, JSON, DateTime, func, ForeignKey, Float, Date, String
from sqlalchemy.orm import relationship

from db.database import Base


class SimulationModel(Base):
    """Portfolio Simulation Result."""

    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True)
    command = Column(String(500), nullable=False)
    tickers = Column(JSON, nullable=False)              # {"AAPL": 0.35}: {str: float}
    weights = Column(JSON, nullable=False)              # {"AAPL": 0.35}: {str: float}
    sides = Column(JSON, nullable=False)                # {"AAPL": "L"}: {str: float}
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    cagr = Column(Float, nullable=True)
    sharpe = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    portfolio_value = Column(JSON, nullable=True)      # {"2020-05-25": 115500.00}: {ISO date: float}
    daily_returns = Column(JSON, nullable=True)        # {"2020-05-25": 1.232}: {ISO date: float}
    cumulative_returns = Column(JSON, nullable=True)   # {"2020-05-25": 115.50000}: {ISO date: float}
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserModel", back_populates="simulations")

    def __repr__(self):
        return f"<Simulation(id={self.id}, {self.start_date}→{self.end_date}, command={self.command}>"

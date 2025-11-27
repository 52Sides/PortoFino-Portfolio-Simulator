from sqlalchemy import Column, Integer, String, Date, Float, DateTime, UniqueConstraint, Index, func

from db.database import Base


class AssetsModel(Base):
    """Fetched data for each ticker"""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(16), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_assets_ticker_date"),
        Index("ix_assets_ticker_date", "ticker", "date"),
    )

    def __repr__(self):
        return f"<Assets(ticker={self.ticker}, date={self.date}, close={self.close})>"

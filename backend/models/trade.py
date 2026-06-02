from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class Trade(Base):
    __tablename__ = "trades"
    id            = Column(Integer, primary_key=True, index=True)
    symbol        = Column(String, nullable=False, index=True)
    exchange      = Column(String, nullable=False)
    direction     = Column(String, nullable=False)
    quantity      = Column(Integer, nullable=False)
    entry_price   = Column(Float, nullable=False)
    exit_price    = Column(Float, nullable=True)
    stop_loss     = Column(Float, nullable=False)
    target        = Column(Float, nullable=False)
    strategy_name = Column(String, nullable=False)
    confidence    = Column(Float, nullable=False)
    is_paper      = Column(Boolean, default=True)
    is_open       = Column(Boolean, default=True)
    pnl           = Column(Float, nullable=True)
    brokerage     = Column(Float, nullable=True)
    net_pnl       = Column(Float, nullable=True)
    entry_time    = Column(DateTime, server_default=func.now())
    exit_time     = Column(DateTime, nullable=True)
    exit_reason   = Column(String, nullable=True)

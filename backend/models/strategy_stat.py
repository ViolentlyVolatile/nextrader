from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from database import Base

class StrategyStat(Base):
    __tablename__    = "strategy_stats"
    id               = Column(Integer, primary_key=True, index=True)
    strategy_name    = Column(String, nullable=False, unique=True, index=True)
    total_trades     = Column(Integer, default=0)
    winning_trades   = Column(Integer, default=0)
    win_rate         = Column(Float, default=0.0)
    sharpe_ratio     = Column(Float, default=0.0)
    max_drawdown     = Column(Float, default=0.0)
    total_pnl        = Column(Float, default=0.0)
    avg_confidence   = Column(Float, default=0.0)
    is_active        = Column(Integer, default=1)
    parameters       = Column(JSON, nullable=True)
    last_updated     = Column(DateTime, server_default=func.now(), onupdate=func.now())

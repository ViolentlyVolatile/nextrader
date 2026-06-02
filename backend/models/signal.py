from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base

class Signal(Base):
    __tablename__          = "signals"
    id                     = Column(Integer, primary_key=True, index=True)
    symbol                 = Column(String, nullable=False, index=True)
    exchange               = Column(String, nullable=False)
    direction              = Column(String, nullable=False)
    strategy_name          = Column(String, nullable=False)
    timeframe              = Column(String, nullable=False)
    confidence             = Column(Float, nullable=False)
    indicator_agreement    = Column(Float, nullable=False)
    volume_confirmation    = Column(Float, nullable=False)
    regime_fit             = Column(Float, nullable=False)
    historical_win_rate    = Column(Float, nullable=False)
    suggested_entry        = Column(Float, nullable=False)
    suggested_sl           = Column(Float, nullable=False)
    suggested_target       = Column(Float, nullable=False)
    risk_reward            = Column(Float, nullable=False)
    signal_data            = Column(JSON, nullable=True)
    acted_on               = Column(Boolean, default=False)
    created_at             = Column(DateTime, server_default=func.now())

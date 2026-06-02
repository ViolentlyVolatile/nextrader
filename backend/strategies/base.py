from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
from config import MIN_CONFIDENCE

@dataclass
class Signal:
    symbol:             str
    exchange:           str
    direction:          str          # BUY | SELL
    timeframe:          str
    indicator_agreement: float       # 0-1
    volume_confirmation: float       # 0-1
    regime_fit:          float       # 0-1
    historical_win_rate: float       # 0-1
    suggested_entry:    float
    suggested_sl:       float
    suggested_target:   float
    strategy_name:      str = ""
    signal_data:        dict = field(default_factory=dict)
    confidence:         float = 0.0

    def __post_init__(self):
        self.confidence = round(min(max((
            self.indicator_agreement  * 0.35 +
            self.historical_win_rate  * 0.30 +
            self.volume_confirmation  * 0.20 +
            self.regime_fit           * 0.15
        ) * 100, 0), 100), 1)

    @property
    def risk_reward(self) -> float:
        risk   = abs(self.suggested_entry - self.suggested_sl)
        reward = abs(self.suggested_target - self.suggested_entry)
        return round(reward / risk, 2) if risk else 0.0

    def passes(self) -> bool:
        return self.confidence >= MIN_CONFIDENCE and self.risk_reward >= 1.5


class BaseStrategy(ABC):
    name: str = "Base"
    default_params: dict = {}

    def __init__(self, params: dict = None):
        self.params    = {**self.default_params, **(params or {})}
        self._win_rate = 0.50

    @abstractmethod
    def generate(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        pass

    def set_win_rate(self, wr: float): self._win_rate = wr

    def _atr(self, df, p=14):
        from indicators import atr
        return atr(df, p).iloc[-1]

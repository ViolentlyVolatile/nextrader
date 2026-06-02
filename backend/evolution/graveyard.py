"""
Strategy Graveyard (Phase 3).
Tracks rolling performance of each strategy and suspends underperformers.
Promotes strategies that consistently outperform.
"""
from datetime import datetime
from typing import Literal


THRESHOLDS = {
    "min_trades":       10,     # need at least 10 trades to evaluate
    "min_win_rate":     0.42,   # suspend if WR < 42%
    "min_sharpe":      -0.3,    # suspend if Sharpe < -0.3
    "min_pf":           0.8,    # watch if profit factor < 0.8
    "promote_wr":       0.55,   # promote if WR > 55%
    "promote_sharpe":   0.5,    # promote if Sharpe > 0.5
    "promote_pf":       1.3,    # promote if PF > 1.3
}

Status = Literal["active", "watch", "suspended", "promoted"]


class StrategyRecord:
    def __init__(self, name: str):
        self.name         = name
        self.status:Status = "active"
        self.total_trades = 0
        self.wins         = 0
        self.total_pnl    = 0.0
        self.sharpe       = 0.0
        self.profit_factor= 0.0
        self.avg_confidence = 0.0
        self._pnl_list: list[float] = []
        self.last_updated = datetime.now().isoformat()
        self.status_reason = "Insufficient trade history"

    @property
    def win_rate(self) -> float:
        return round(self.wins / self.total_trades, 4) if self.total_trades else 0.0

    def record_trade(self, net_pnl: float, confidence: float):
        self.total_trades += 1
        self.total_pnl    += net_pnl
        self._pnl_list.append(net_pnl)
        if net_pnl > 0:
            self.wins += 1
        # Rolling confidence average
        self.avg_confidence = round(
            (self.avg_confidence * (self.total_trades - 1) + confidence) / self.total_trades, 2
        )
        # Simple profit factor
        gross_wins  = sum(p for p in self._pnl_list if p > 0)
        gross_losses = abs(sum(p for p in self._pnl_list if p < 0))
        self.profit_factor = round(gross_wins / gross_losses, 3) if gross_losses else float("inf")
        # Approximate Sharpe from PnL list
        if len(self._pnl_list) >= 5:
            import numpy as np
            arr = np.array(self._pnl_list)
            self.sharpe = round(float(arr.mean() / (arr.std() + 1e-8)), 3)
        self.last_updated = datetime.now().isoformat()
        self._evaluate()

    def _evaluate(self):
        if self.total_trades < THRESHOLDS["min_trades"]:
            self.status_reason = f"Building history ({self.total_trades}/{THRESHOLDS['min_trades']} trades)"
            return

        if (self.win_rate > THRESHOLDS["promote_wr"] and
                self.sharpe > THRESHOLDS["promote_sharpe"] and
                self.profit_factor > THRESHOLDS["promote_pf"]):
            self.status = "promoted"
            self.status_reason = f"High performer: WR={self.win_rate:.1%} Sharpe={self.sharpe:.2f}"
            return

        if self.win_rate < THRESHOLDS["min_win_rate"]:
            self.status = "suspended"
            self.status_reason = f"WR {self.win_rate:.1%} below threshold {THRESHOLDS['min_win_rate']:.1%}"
            return

        if self.sharpe < THRESHOLDS["min_sharpe"]:
            self.status = "suspended"
            self.status_reason = f"Sharpe {self.sharpe:.2f} below threshold {THRESHOLDS['min_sharpe']}"
            return

        if self.profit_factor < THRESHOLDS["min_pf"]:
            self.status = "watch"
            self.status_reason = f"PF {self.profit_factor:.2f} below threshold {THRESHOLDS['min_pf']}"
            return

        self.status = "active"
        self.status_reason = "Performing adequately"

    def to_dict(self) -> dict:
        return {
            "name":           self.name,
            "status":         self.status,
            "status_reason":  self.status_reason,
            "total_trades":   self.total_trades,
            "win_rate":       self.win_rate,
            "total_pnl":      round(self.total_pnl, 2),
            "sharpe":         self.sharpe,
            "profit_factor":  self.profit_factor,
            "avg_confidence": self.avg_confidence,
            "last_updated":   self.last_updated,
        }


class StrategyGraveyard:
    """Singleton registry of all strategy performance records."""

    def __init__(self, strategy_names: list[str]):
        self._records = {n: StrategyRecord(n) for n in strategy_names}

    def record(self, strategy_name: str, net_pnl: float, confidence: float):
        if strategy_name in self._records:
            self._records[strategy_name].record_trade(net_pnl, confidence)

    def is_active(self, strategy_name: str) -> bool:
        rec = self._records.get(strategy_name)
        return rec is None or rec.status != "suspended"

    def all_records(self) -> list[dict]:
        return [r.to_dict() for r in self._records.values()]

    def summary(self) -> dict:
        recs = list(self._records.values())
        return {
            "total":     len(recs),
            "active":    sum(1 for r in recs if r.status == "active"),
            "watch":     sum(1 for r in recs if r.status == "watch"),
            "suspended": sum(1 for r in recs if r.status == "suspended"),
            "promoted":  sum(1 for r in recs if r.status == "promoted"),
        }

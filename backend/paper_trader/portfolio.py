"""
Paper trading virtual portfolio.
Tracks open positions, live unrealised P&L, and trade history.
Extends the backtester Portfolio with real-time price updates.
"""
from dataclasses import dataclass, field
from datetime import datetime
from engine import calc_brokerage
from config import STARTING_CAPITAL


@dataclass
class PaperPosition:
    symbol:     str
    direction:  str         # BUY | SELL
    quantity:   int
    entry:      float
    stop_loss:  float
    target:     float
    strategy:   str
    confidence: float
    opened_at:  str = field(default_factory=lambda: datetime.now().isoformat())
    current:    float = 0.0

    @property
    def unrealised_pnl(self) -> float:
        if self.direction == "BUY":
            return round((self.current - self.entry) * self.quantity, 2)
        return round((self.entry - self.current) * self.quantity, 2)

    @property
    def pnl_pct(self) -> float:
        cost = self.entry * self.quantity
        return round(self.unrealised_pnl / cost * 100, 3) if cost else 0.0

    def to_dict(self) -> dict:
        return {
            "symbol":         self.symbol,
            "direction":      self.direction,
            "quantity":       self.quantity,
            "entry":          self.entry,
            "current":        round(self.current, 2),
            "stop_loss":      self.stop_loss,
            "target":         self.target,
            "strategy":       self.strategy,
            "confidence":     self.confidence,
            "unrealised_pnl": self.unrealised_pnl,
            "pnl_pct":        self.pnl_pct,
            "opened_at":      self.opened_at,
        }


class PaperPortfolio:
    def __init__(self, starting_capital: float = STARTING_CAPITAL):
        self.starting_capital = starting_capital
        self.capital          = starting_capital
        self._positions: dict[str, PaperPosition] = {}
        self._closed:    list[dict]                = []
        self.equity_curve: list[dict]              = [
            {"t": datetime.now().isoformat(), "v": starting_capital}
        ]

    # ── position management ──────────────────────────────────────────────────

    def open_position(self, symbol, direction, qty, entry, sl, tgt, strategy, conf) -> bool:
        if symbol in self._positions:
            return False  # already open
        cost = entry * qty
        if cost > self.capital:
            return False
        self.capital -= cost
        self._positions[symbol] = PaperPosition(
            symbol=symbol, direction=direction, quantity=qty,
            entry=entry, stop_loss=sl, target=tgt,
            strategy=strategy, confidence=conf, current=entry
        )
        return True

    def close_position(self, symbol: str, exit_price: float, reason: str) -> dict:
        if symbol not in self._positions:
            return {}
        pos   = self._positions.pop(symbol)
        gross = (exit_price - pos.entry) * pos.quantity if pos.direction == "BUY" \
                else (pos.entry - exit_price) * pos.quantity
        brok  = calc_brokerage(pos.entry, exit_price, pos.quantity)
        net   = gross - brok
        self.capital += pos.entry * pos.quantity + net
        self.equity_curve.append({"t": datetime.now().isoformat(), "v": round(self.capital, 2)})
        record = {
            "symbol": symbol, "direction": pos.direction, "quantity": pos.quantity,
            "entry": pos.entry, "exit": round(exit_price, 2),
            "gross_pnl": round(gross, 2), "brokerage": round(brok, 2),
            "net_pnl": round(net, 2), "reason": reason,
            "strategy": pos.strategy, "confidence": pos.confidence,
            "opened_at": pos.opened_at, "closed_at": datetime.now().isoformat(),
        }
        self._closed.append(record)
        return record

    def update_price(self, symbol: str, price: float):
        if symbol in self._positions:
            self._positions[symbol].current = price

    def check_stops(self, symbol: str) -> str | None:
        if symbol not in self._positions:
            return None
        pos = self._positions[symbol]
        if pos.direction == "BUY":
            if pos.current <= pos.stop_loss:  return "SL"
            if pos.current >= pos.target:     return "TARGET"
        else:
            if pos.current >= pos.stop_loss:  return "SL"
            if pos.current <= pos.target:     return "TARGET"
        return None

    # ── snapshots ────────────────────────────────────────────────────────────

    @property
    def open_count(self) -> int:
        return len(self._positions)

    @property
    def total_unrealised(self) -> float:
        return round(sum(p.unrealised_pnl for p in self._positions.values()), 2)

    @property
    def total_realised(self) -> float:
        return round(sum(t["net_pnl"] for t in self._closed), 2)

    def snapshot(self) -> dict:
        return {
            "capital":          round(self.capital, 2),
            "starting_capital": self.starting_capital,
            "open_positions":   self.open_count,
            "unrealised_pnl":   self.total_unrealised,
            "realised_pnl":     self.total_realised,
            "total_pnl":        round(self.total_unrealised + self.total_realised, 2),
            "total_pnl_pct":    round((self.total_unrealised + self.total_realised) / self.starting_capital * 100, 3),
            "positions":        [p.to_dict() for p in self._positions.values()],
            "closed_count":     len(self._closed),
            "timestamp":        datetime.now().isoformat(),
        }

    def recent_trades(self, n: int = 50) -> list[dict]:
        return self._closed[-n:]

    def win_rate(self) -> float:
        if not self._closed: return 0.0
        wins = sum(1 for t in self._closed if t["net_pnl"] > 0)
        return round(wins / len(self._closed), 4)

"""
Live feed handler.
- MockLiveFeed: replays/extrapolates from last known prices (demo mode)
- KiteLiveFeed: real Zerodha WebSocket (Phase 4, requires access token)
"""
import asyncio
import random
from datetime import datetime
from typing import Callable


class MockLiveFeed:
    """Simulates live NSE ticks via random walk from seed prices."""

    def __init__(self, seed_prices: dict[str, float]):
        self.prices    = {s: float(p) for s, p in seed_prices.items()}
        self._running  = False
        self._callbacks: list[Callable] = []

    def subscribe(self, cb: Callable):
        self._callbacks.append(cb)

    async def start(self):
        self._running = True
        while self._running:
            for symbol, price in list(self.prices.items()):
                # Random walk ±0.08% per tick (realistic intraday noise)
                change   = price * random.uniform(-0.0008, 0.0008)
                new_price = round(max(price + change, 1.0), 2)
                self.prices[symbol] = new_price

                tick = {
                    "symbol":    symbol,
                    "price":     new_price,
                    "change":    round(change, 2),
                    "change_pct": round(change / price * 100, 4),
                    "volume":    random.randint(5_000, 200_000),
                    "timestamp": datetime.now().isoformat(),
                }
                for cb in self._callbacks:
                    try:
                        await cb(tick)
                    except Exception:
                        pass

            await asyncio.sleep(1)   # 1 tick/sec — realistic for NSE

    def stop(self):
        self._running = False

    def get_price(self, symbol: str) -> float | None:
        return self.prices.get(symbol)

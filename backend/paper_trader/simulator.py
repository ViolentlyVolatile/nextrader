"""
Paper Trading Simulator (Phase 2).
Runs all 12 strategies against live ticks, executes virtual trades,
tracks P&L in real-time, streams everything to the React dashboard via WebSocket.
"""
import asyncio
from datetime import datetime
from data import fetch_daily
from engine import Orchestrator, RiskManager
from paper_trader.live_feed import MockLiveFeed
from paper_trader.portfolio import PaperPortfolio
from api.websocket import manager
from config import STARTING_CAPITAL, MAX_POSITIONS
from data import get_universe

# ── Singleton state ──────────────────────────────────────────────────────────
_simulator: "PaperSimulator | None" = None

def get_simulator() -> "PaperSimulator | None":
    return _simulator

def set_simulator(sim):
    global _simulator
    _simulator = sim


class PaperSimulator:
    def __init__(self, symbols: list[str] | None = None):
        self.symbols     = symbols or [s for s, _ in get_universe()[:12]]
        self.portfolio   = PaperPortfolio(STARTING_CAPITAL)
        self.risk        = RiskManager(STARTING_CAPITAL)
        self.orchestrator = Orchestrator()
        self._running    = False
        self._feed: MockLiveFeed | None = None
        self.signal_log: list[dict]     = []
        self._scan_task  = None
        self._feed_task  = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        # Seed prices from sample data last close
        seed = {}
        for sym in self.symbols:
            df = await fetch_daily(sym, "NSE", 30)
            if df is not None and len(df) > 0:
                seed[sym] = float(df["close"].iloc[-1])
        if not seed:
            seed = {s: 1000.0 for s in self.symbols}

        self._feed = MockLiveFeed(seed)
        self._feed.subscribe(self._on_tick)

        # Run feed + signal scanner concurrently
        self._feed_task = asyncio.create_task(self._feed.start())
        self._scan_task = asyncio.create_task(self._signal_loop())

    def stop(self):
        self._running = False
        if self._feed:      self._feed.stop()
        if self._feed_task: self._feed_task.cancel()
        if self._scan_task: self._scan_task.cancel()

    # ── tick handler ──────────────────────────────────────────────────────────

    async def _on_tick(self, tick: dict):
        sym   = tick["symbol"]
        price = tick["price"]

        # Update portfolio with latest price
        self.portfolio.update_price(sym, price)

        # Check stop loss / target on open positions
        reason = self.portfolio.check_stops(sym)
        if reason:
            pos     = self.portfolio._positions.get(sym)
            ep      = pos.stop_loss if reason == "SL" else pos.target
            record  = self.portfolio.close_position(sym, ep, reason)
            self.risk.remove()
            self.risk.update(record.get("net_pnl", 0))
            await manager.broadcast({
                "type":   "trade_closed",
                "data":   record,
                "portfolio": self.portfolio.snapshot(),
            })

        # Broadcast tick + portfolio snapshot every tick
        await manager.broadcast({
            "type":      "tick",
            "data":      tick,
            "portfolio": self.portfolio.snapshot(),
        })

    # ── signal scanner ────────────────────────────────────────────────────────

    async def _signal_loop(self):
        """Re-scans all symbols every 5 minutes for new signals."""
        while self._running:
            for sym in self.symbols:
                if not self._running:
                    break
                try:
                    df = await fetch_daily(sym, "NSE", 200)
                    if df is None or len(df) < 60:
                        continue

                    result    = self.orchestrator.run(sym, df)
                    consensus = result.get("consensus")
                    all_sigs  = result.get("signals", [])

                    # Broadcast all individual signals to UI regardless of consensus
                    if all_sigs:
                        await manager.broadcast({
                            "type":   "signals",
                            "symbol": sym,
                            "regime": result.get("regime", "UNKNOWN"),
                            "signals": all_sigs,
                            "consensus": consensus,
                        })

                    # Only trade on consensus
                    if consensus:
                        can, _ = self.risk.can_trade()
                        if can and self.portfolio.open_count < MAX_POSITIONS:
                            entry = consensus["entry"]
                            sl    = consensus["sl"]
                            tgt   = consensus["target"]
                            qty   = self.risk.size(entry, sl, 0.55)
                            if qty > 0:
                                opened = self.portfolio.open_position(
                                    sym, consensus["direction"], qty,
                                    entry, sl, tgt,
                                    "Consensus", consensus["avg_confidence"]
                                )
                                if opened:
                                    self.risk.add()
                                    log = {
                                        **consensus,
                                        "symbol":    sym,
                                        "quantity":  qty,
                                        "timestamp": datetime.now().isoformat(),
                                        "all_signals": all_sigs,
                                    }
                                    self.signal_log.insert(0, log)
                                    if len(self.signal_log) > 200:
                                        self.signal_log.pop()
                                    await manager.broadcast({
                                        "type":      "trade_opened",
                                        "data":      log,
                                        "portfolio": self.portfolio.snapshot(),
                                    })
                except Exception as e:
                    print(f"[PaperSim] Error scanning {sym}: {e}")

            # Wait 5 minutes before next scan
            for _ in range(300):
                if not self._running:
                    break
                await asyncio.sleep(1)

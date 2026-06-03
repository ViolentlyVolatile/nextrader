"""
Backtesting engine — optimised single-pass approach.
Pre-computes all indicator values once, then steps through bars O(n) not O(n²).
"""
import pandas as pd
import numpy as np
from engine import RiskManager, calc_brokerage
from config import STARTING_CAPITAL, MAX_POSITIONS
import indicators as ind


# ── METRICS ───────────────────────────────────────────────────────────────────

def sharpe(returns: pd.Series, rf=0.065, periods=252) -> float:
    if len(returns) < 2 or returns.std() == 0: return 0.0
    ex = returns - rf / periods
    return round(float(ex.mean() / ex.std() * np.sqrt(periods)), 3)

def max_dd(equity: pd.Series) -> float:
    rm = equity.cummax()
    return round(float(((equity - rm) / rm).min()), 4)

def summary(trades: pd.DataFrame, equity: list, start_cap: float) -> dict:
    ec  = pd.Series(equity)
    ret = ec.pct_change().dropna()
    wr  = float((trades["net_pnl"] > 0).mean()) if len(trades) else 0.0
    wins   = trades[trades["net_pnl"] > 0]["net_pnl"].sum() if len(trades) else 0
    losses = abs(trades[trades["net_pnl"] < 0]["net_pnl"].sum()) if len(trades) else 1
    pf  = round(wins / losses, 3) if losses else float("inf")
    pnl = float(ec.iloc[-1] - start_cap) if len(ec) > 1 else 0
    return {
        "total_trades":    len(trades),
        "win_rate":        round(wr, 4),
        "profit_factor":   pf,
        "sharpe_ratio":    sharpe(ret),
        "max_drawdown_pct": max_dd(ec),
        "total_pnl":       round(pnl, 2),
        "total_pnl_pct":   round(pnl / start_cap * 100, 2),
        "final_capital":   round(float(ec.iloc[-1]), 2) if len(ec) > 1 else start_cap,
    }


# ── FAST SIGNAL GENERATOR ─────────────────────────────────────────────────────
# Pre-compute signals for all bars at once instead of re-running strategies each bar

def _precompute_signals(df: pd.DataFrame) -> pd.Series:
    """
    Returns a Series indexed by bar position with values:
      'BUY', 'SELL', or None
    Uses vectorised indicator maths — runs once, not per-bar.
    """
    n    = len(df)
    sigs = [None] * n
    c    = df["close"]
    h    = df["high"]
    l    = df["low"]
    v    = df["volume"]

    # Pre-compute all indicators once
    rsi_s      = ind.rsi(df, 14)
    ema9       = ind.ema(df, 9)
    ema21      = ind.ema(df, 21)
    ema50      = ind.ema(df, 50)
    macd_l, macd_sig, macd_h = ind.macd(df)
    adx_s, dip, dim = ind.adx(df, 14)
    ub, mb, lb = ind.bollinger(df, 20)
    atr_s      = ind.atr(df, 14)
    vol_r      = ind.vol_ratio(df, 20)
    st, st_dir = ind.supertrend(df, 7, 3.0)
    sar_s      = ind.parabolic_sar(df)
    stoch_k, stoch_d = ind.stochastic(df, 14, 3, 3)
    roc_s      = ind.roc(df, 10)
    sqz        = ind.bb_squeeze(df)
    be         = ind.bull_engulf(df)
    beare      = ind.bear_engulf(df)
    pb         = ind.pin_bull(df)
    pbr        = ind.pin_bear(df)

    min_bar = 80  # minimum bars needed for all indicators to be valid

    for i in range(min_bar, n):
        buy_votes  = 0
        sell_votes = 0
        atr_val    = atr_s.iloc[i]
        if pd.isna(atr_val) or atr_val <= 0:
            continue

        # 1. MomentumRSI
        r = rsi_s.iloc[i]; rc = roc_s.iloc[i]
        if not pd.isna(r) and not pd.isna(rc):
            if r < 35 and rc > 0:  buy_votes  += 1
            if r > 65 and rc < 0:  sell_votes += 1

        # 2. EMACrossover
        if not any(pd.isna([ema9.iloc[i], ema21.iloc[i], ema9.iloc[i-1], ema21.iloc[i-1]])):
            if ema9.iloc[i-1] <= ema21.iloc[i-1] and ema9.iloc[i] > ema21.iloc[i]:
                buy_votes  += 1
            if ema9.iloc[i-1] >= ema21.iloc[i-1] and ema9.iloc[i] < ema21.iloc[i]:
                sell_votes += 1

        # 3. SupertrendADX
        adx_v = adx_s.iloc[i]
        if not pd.isna(adx_v) and adx_v > 25 and st_dir.iloc[i] != st_dir.iloc[i-1]:
            if st_dir.iloc[i] == 1:  buy_votes  += 1
            if st_dir.iloc[i] == -1: sell_votes += 1

        # 4. BollingerSqueeze
        if sqz.iloc[i-1] == 1 and sqz.iloc[i] == 0:
            if c.iloc[i] > ub.iloc[i-1] or rsi_s.iloc[i] > 55: buy_votes  += 1
            else:                                                  sell_votes += 1

        # 5. MACD Divergence
        if i >= 10:
            ps = c.iloc[i-10:i].diff().mean()
            hs = macd_h.iloc[i-10:i].diff().mean()
            if not any(pd.isna([ps, hs, macd_h.iloc[i]])):
                if ps < 0 and hs > 0 and macd_h.iloc[i] < 0: buy_votes  += 1
                if ps > 0 and hs < 0 and macd_h.iloc[i] > 0: sell_votes += 1

        # 6. Stochastic
        if not any(pd.isna([stoch_k.iloc[i], stoch_d.iloc[i], stoch_k.iloc[i-1], stoch_d.iloc[i-1]])):
            cu = stoch_k.iloc[i-1] <= stoch_d.iloc[i-1] and stoch_k.iloc[i] > stoch_d.iloc[i] and stoch_k.iloc[i] < 35
            cd = stoch_k.iloc[i-1] >= stoch_d.iloc[i-1] and stoch_k.iloc[i] < stoch_d.iloc[i] and stoch_k.iloc[i] > 65
            if cu: buy_votes  += 1
            if cd: sell_votes += 1

        # 7. PriceAction patterns
        if be.iloc[i] or pb.iloc[i]:  buy_votes  += 1
        if beare.iloc[i] or pbr.iloc[i]: sell_votes += 1

        # 8. ParabolicSAR + EMA50
        if not any(pd.isna([sar_s.iloc[i], sar_s.iloc[i-1], ema50.iloc[i]])):
            sar_flip_up   = sar_s.iloc[i-1] > c.iloc[i-1] and sar_s.iloc[i] < c.iloc[i]
            sar_flip_down = sar_s.iloc[i-1] < c.iloc[i-1] and sar_s.iloc[i] > c.iloc[i]
            if sar_flip_up   and c.iloc[i] > ema50.iloc[i]: buy_votes  += 1
            if sar_flip_down and c.iloc[i] < ema50.iloc[i]: sell_votes += 1

        # Consensus: need 2+ strategies agreeing
        if buy_votes >= 2 and buy_votes > sell_votes:
            sigs[i] = "BUY"
        elif sell_votes >= 2 and sell_votes > buy_votes:
            sigs[i] = "SELL"

    return pd.Series(sigs, index=df.index)


# ── PORTFOLIO ─────────────────────────────────────────────────────────────────

class _Trade:
    def __init__(self, symbol, direction, qty, entry, sl, tgt, conf):
        self.symbol = symbol; self.direction = direction; self.qty = qty
        self.entry = entry; self.sl = sl; self.tgt = tgt; self.conf = conf

class Portfolio:
    def __init__(self, capital):
        self.capital = capital
        self._open:   dict[str, _Trade] = {}
        self._closed: list[dict]        = []
        self.equity:  list[float]       = [capital]

    @property
    def open_pos(self): return len(self._open)

    def open(self, symbol, direction, qty, entry, sl, tgt, conf) -> bool:
        if entry * qty > self.capital: return False
        self.capital -= entry * qty
        self._open[symbol] = _Trade(symbol, direction, qty, entry, sl, tgt, conf)
        return True

    def close(self, symbol, exit_price, reason) -> dict:
        if symbol not in self._open: return {}
        t     = self._open.pop(symbol)
        gross = (exit_price - t.entry) * t.qty if t.direction == "BUY" \
                else (t.entry - exit_price) * t.qty
        brok  = calc_brokerage(t.entry, exit_price, t.qty)
        net   = gross - brok
        self.capital += t.entry * t.qty + net
        rec = {"symbol": symbol, "direction": t.direction, "quantity": t.qty,
               "entry_price": t.entry, "exit_price": round(exit_price, 2),
               "gross_pnl": round(gross, 2), "brokerage": round(brok, 2),
               "net_pnl": round(net, 2), "reason": reason,
               "strategy": "Consensus", "confidence": t.conf}
        self._closed.append(rec)
        self.equity.append(self.capital)
        return rec

    def check_stops(self, symbol, high, low):
        if symbol not in self._open: return None
        t = self._open[symbol]
        if t.direction == "BUY":
            if low  <= t.sl:  return "SL"
            if high >= t.tgt: return "TARGET"
        else:
            if high >= t.sl:  return "SL"
            if low  <= t.tgt: return "TARGET"
        return None

    def trades_df(self): return pd.DataFrame(self._closed)


# ── BACKTESTER ────────────────────────────────────────────────────────────────

class Backtester:
    def __init__(self, capital: float = STARTING_CAPITAL):
        self.capital = capital

    def run(self, symbol: str, df: pd.DataFrame, params: dict = None) -> dict:
        if df is None or len(df) < 90:
            return {"error": f"Need 90+ bars, got {len(df) if df is not None else 0}"}

        # Pre-compute all signals in one pass — FAST
        signals = _precompute_signals(df)

        risk = RiskManager(self.capital)
        port = Portfolio(self.capital)

        for i in range(len(df)):
            bar = df.iloc[i]

            # Check stops on open position
            if symbol in port._open:
                reason = port.check_stops(symbol, bar["high"], bar["low"])
                if reason:
                    t   = port._open[symbol]
                    ep  = t.sl if reason == "SL" else t.tgt
                    rec = port.close(symbol, ep, reason)
                    risk.remove(); risk.update(rec.get("net_pnl", 0))

            # Check for signal on this bar
            sig = signals.iloc[i]
            if sig and port.open_pos < MAX_POSITIONS:
                ok, _ = risk.can_trade()
                if ok:
                    price = bar["close"]
                    atr_v = (bar["high"] - bar["low"]) * 1.5
                    if atr_v <= 0: continue
                    sl  = price - atr_v if sig == "BUY" else price + atr_v
                    tgt = price + atr_v * 2 if sig == "BUY" else price - atr_v * 2
                    qty = risk.size(price, sl, 0.55)
                    if qty > 0:
                        opened = port.open(symbol, sig, qty, price, sl, tgt, 65.0)
                        if opened: risk.add()

        # Close remaining at last price
        if symbol in port._open:
            port.close(symbol, df["close"].iloc[-1], "EOD")

        trades = port.trades_df()
        result = summary(trades, port.equity, self.capital)
        result.update({
            "symbol":       symbol,
            "equity_curve": port.equity,
            "trades":       trades.to_dict(orient="records") if len(trades) else [],
        })
        return result

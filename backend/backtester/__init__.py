import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from engine import Orchestrator, RiskManager, calc_brokerage, detect_regime
from config import STARTING_CAPITAL, MAX_POSITIONS


# ── METRICS ───────────────────────────────────────────────────────────────────

def sharpe(returns: pd.Series, rf=0.065, periods=252) -> float:
    if len(returns)<2 or returns.std()==0: return 0.0
    ex = returns - rf/periods
    return round(float(ex.mean()/ex.std()*np.sqrt(periods)), 3)

def max_dd(equity: pd.Series) -> float:
    rm = equity.cummax()
    return round(float(((equity-rm)/rm).min()), 4)

def summary(trades: pd.DataFrame, equity: list, start_cap: float) -> dict:
    ec  = pd.Series(equity)
    ret = ec.pct_change().dropna()
    wr  = float((trades["net_pnl"]>0).mean()) if len(trades) else 0.0
    wins   = trades[trades["net_pnl"]>0]["net_pnl"].sum() if len(trades) else 0
    losses = abs(trades[trades["net_pnl"]<0]["net_pnl"].sum()) if len(trades) else 1
    pf  = round(wins/losses,3) if losses else float("inf")
    pnl = float(ec.iloc[-1]-start_cap) if len(ec)>1 else 0
    return {"total_trades":len(trades),"win_rate":round(wr,4),
            "profit_factor":pf,"sharpe_ratio":sharpe(ret),
            "max_drawdown_pct":max_dd(ec),"total_pnl":round(pnl,2),
            "total_pnl_pct":round(pnl/start_cap*100,2),
            "final_capital":round(float(ec.iloc[-1]),2) if len(ec)>1 else start_cap}


# ── VIRTUAL PORTFOLIO ─────────────────────────────────────────────────────────

@dataclass
class _Trade:
    symbol:str; direction:str; qty:int; entry:float; sl:float; tgt:float; strategy:str; conf:float

class Portfolio:
    def __init__(self, capital: float):
        self.capital      = capital
        self._open: dict[str,_Trade] = {}
        self._closed: list[dict]     = []
        self.equity: list[float]     = [capital]

    @property
    def open_pos(self): return len(self._open)

    def open(self, symbol,direction,qty,entry,sl,tgt,strategy,conf) -> bool:
        if entry*qty>self.capital: return False
        self.capital -= entry*qty
        self._open[symbol] = _Trade(symbol,direction,qty,entry,sl,tgt,strategy,conf)
        return True

    def close(self, symbol, exit_price, reason) -> dict:
        if symbol not in self._open: return {}
        t = self._open.pop(symbol)
        gross = (exit_price-t.entry)*t.qty if t.direction=="BUY" else (t.entry-exit_price)*t.qty
        brok  = calc_brokerage(t.entry, exit_price, t.qty)
        net   = gross - brok
        self.capital += t.entry*t.qty + net
        r = {"symbol":symbol,"direction":t.direction,"quantity":t.qty,
             "entry_price":t.entry,"exit_price":exit_price,
             "gross_pnl":round(gross,2),"brokerage":round(brok,2),
             "net_pnl":round(net,2),"reason":reason,
             "strategy":t.strategy,"confidence":t.conf}
        self._closed.append(r)
        self.equity.append(self.capital)
        return r

    def check_stops(self, symbol, high, low) -> str | None:
        if symbol not in self._open: return None
        t = self._open[symbol]
        if t.direction=="BUY":
            if low<=t.sl:  return "SL"
            if high>=t.tgt: return "TARGET"
        else:
            if high>=t.sl:  return "SL"
            if low<=t.tgt:  return "TARGET"
        return None

    def trades_df(self) -> pd.DataFrame:
        return pd.DataFrame(self._closed)


# ── BACKTEST ENGINE ───────────────────────────────────────────────────────────

class Backtester:
    def __init__(self, capital: float = STARTING_CAPITAL):
        self.capital = capital

    def run(self, symbol: str, df: pd.DataFrame, params: dict = None) -> dict:
        if df is None or len(df)<90:
            return {"error":f"Need 90+ bars, got {len(df) if df is not None else 0}"}
        orc  = Orchestrator(params)
        risk = RiskManager(self.capital)
        port = Portfolio(self.capital)
        lb   = 80

        for i in range(lb, len(df)):
            hist = df.iloc[:i].copy()
            bar  = df.iloc[i]

            # Check open stops
            if symbol in port._open:
                reason = port.check_stops(symbol, bar["high"], bar["low"])
                if reason:
                    ep = port._open[symbol].sl if reason=="SL" else port._open[symbol].tgt
                    rec = port.close(symbol, ep, reason)
                    risk.remove(); risk.update(rec.get("net_pnl",0))

            # Generate signals
            res = orc.run(symbol, hist)
            con = res.get("consensus")
            if con and port.open_pos<MAX_POSITIONS:
                ok,_ = risk.can_trade()
                if ok:
                    entry=con["entry"]; sl_=con["sl"]; tgt_=con["target"]
                    qty=risk.size(entry,sl_,0.55)
                    if qty>0:
                        opened=port.open(symbol,con["direction"],qty,entry,sl_,tgt_,"Consensus",con["avg_confidence"])
                        if opened: risk.add()

        # Close remaining
        if symbol in port._open:
            port.close(symbol, df["close"].iloc[-1], "EOD")

        trades = port.trades_df()
        result = summary(trades, port.equity, self.capital)
        result.update({"symbol":symbol,
                       "equity_curve":port.equity,
                       "trades":trades.to_dict(orient="records") if len(trades) else []})
        return result

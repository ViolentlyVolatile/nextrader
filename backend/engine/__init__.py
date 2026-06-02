import pandas as pd
import numpy as np
from typing import Optional
from strategies import ALL_STRATEGIES
from config import (CONSENSUS_MIN_COUNT, CONSENSUS_MIN_CONF, MAX_RISK,
                    MAX_POSITIONS, DAILY_LOSS_LIMIT, KELLY_CAP, STARTING_CAPITAL,
                    BROKERAGE_PER_ORDER, STT_PCT, EXCHANGE_PCT, GST_PCT)


# ── REGIME DETECTOR ──────────────────────────────────────────────────────────

def detect_regime(df: pd.DataFrame) -> str:
    if len(df)<50: return "UNKNOWN"
    import indicators as ind
    adx_,_,__=ind.adx(df)
    a=adx_.iloc[-1]
    if pd.isna(a): return "UNKNOWN"
    bb_w=(2*df["close"].rolling(20).std()/df["close"].rolling(20).mean())
    return "TRENDING" if a>25 else ("VOLATILE" if bb_w.iloc[-1]>bb_w.mean()*1.5 else "RANGING")


# ── BROKERAGE ─────────────────────────────────────────────────────────────────

def calc_brokerage(entry: float, exit_: float, qty: int) -> float:
    turnover = (entry+exit_)*qty
    brok     = BROKERAGE_PER_ORDER*2
    stt      = exit_*qty*STT_PCT
    exch     = turnover*EXCHANGE_PCT
    gst      = (brok+exch)*GST_PCT
    return round(brok+stt+exch+gst, 2)


# ── RISK MANAGER ──────────────────────────────────────────────────────────────

class RiskManager:
    def __init__(self, capital: float = STARTING_CAPITAL):
        self.capital       = capital
        self.open_pos      = 0
        self.daily_pnl     = 0.0
        self.halted        = False

    def can_trade(self) -> tuple[bool, str]:
        if self.halted:            return False, "Halted: daily loss limit breached"
        if self.open_pos>=MAX_POSITIONS: return False, f"Max {MAX_POSITIONS} positions open"
        if self.daily_pnl<=-DAILY_LOSS_LIMIT: self.halted=True; return False,"Daily limit breached"
        return True, "OK"

    def size(self, entry: float, sl: float, wr: float) -> int:
        risk_per = abs(entry-sl)
        if risk_per<=0: return 0
        fixed    = int(MAX_RISK/risk_per)
        rr=2.0; kf=max(min((wr*rr-(1-wr))/rr, KELLY_CAP), 0.01)
        kelly    = int(self.capital*kf/entry)
        return max(min(fixed,kelly),1)

    def update(self, pnl: float):
        self.daily_pnl+=pnl; self.capital+=pnl
        if self.daily_pnl<=-DAILY_LOSS_LIMIT: self.halted=True

    def reset_day(self): self.daily_pnl=0.0; self.halted=False
    def add(self):       self.open_pos+=1
    def remove(self):    self.open_pos=max(0,self.open_pos-1)


# ── ORCHESTRATOR ──────────────────────────────────────────────────────────────

class Orchestrator:
    def __init__(self, params: dict = None):
        self.strategies = [cls(params.get(cls.name,{}) if params else {}) for cls in ALL_STRATEGIES]

    def run(self, symbol: str, df: pd.DataFrame) -> dict:
        if df is None or len(df)<60:
            return {"symbol":symbol,"signals":[],"consensus":None,"regime":"UNKNOWN"}
        regime = detect_regime(df)
        signals = []
        for s in self.strategies:
            try:
                sig=s.generate(df, symbol)
                if sig: signals.append(sig)
            except Exception as e:
                pass  # silent — strategy errors don't crash the engine

        consensus = self._consensus(symbol, signals)
        return {
            "symbol":  symbol,
            "regime":  regime,
            "signals": [{"strategy":s.strategy_name,"direction":s.direction,
                         "confidence":s.confidence,"entry":s.suggested_entry,
                         "sl":s.suggested_sl,"target":s.suggested_target,
                         "rr":s.risk_reward,"data":s.signal_data} for s in signals],
            "consensus": consensus
        }

    def _consensus(self, symbol: str, signals: list) -> Optional[dict]:
        if not signals: return None
        buys  = [s for s in signals if s.direction=="BUY"]
        sells = [s for s in signals if s.direction=="SELL"]
        dom   = buys if len(buys)>=len(sells) else sells
        dir_  = "BUY" if dom is buys else "SELL"
        if len(dom)<CONSENSUS_MIN_COUNT: return None
        avg_c = sum(s.confidence for s in dom)/len(dom)
        if avg_c<CONSENSUS_MIN_CONF: return None
        best  = max(dom, key=lambda s: s.confidence)
        return {"symbol":symbol,"direction":dir_,"avg_confidence":round(avg_c,1),
                "agreeing":len(dom),"total":len(signals),
                "entry":best.suggested_entry,"sl":best.suggested_sl,
                "target":best.suggested_target,"rr":best.risk_reward,
                "strategies":[{"name":s.strategy_name,"confidence":s.confidence} for s in dom]}

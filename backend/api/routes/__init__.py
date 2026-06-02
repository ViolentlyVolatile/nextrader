from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from data import fetch_daily, get_universe
from backtester import Backtester
from engine import Orchestrator
from strategies import ALL_STRATEGIES
from config import STARTING_CAPITAL, MAX_RISK, MAX_POSITIONS, DAILY_LOSS_LIMIT

router = APIRouter()
_results: dict = {}   # in-memory backtest cache
_scan_cache: dict = {}


# ── SYSTEM ────────────────────────────────────────────────────────────────────

@router.get("/api/health")
async def health():
    return {"status":"ok","version":"1.0.0","phase":"Phase 1 — Core Engine"}

@router.get("/api/system/config")
async def system_config():
    return {"starting_capital":STARTING_CAPITAL,"max_risk_per_trade":MAX_RISK,
            "max_open_positions":MAX_POSITIONS,"daily_loss_limit":DAILY_LOSS_LIMIT}

@router.get("/api/universe")
async def universe():
    return {"stocks":[{"symbol":s,"exchange":e} for s,e in get_universe()]}


# ── STRATEGIES ────────────────────────────────────────────────────────────────

@router.get("/api/strategies")
async def strategies():
    return {"strategies":[{"name":cls.name,"params":cls.default_params} for cls in ALL_STRATEGIES],
            "total": len(ALL_STRATEGIES)}


# ── BACKTEST ──────────────────────────────────────────────────────────────────

class BacktestReq(BaseModel):
    symbol:           str
    exchange:         str   = "NSE"
    days:             int   = 365
    starting_capital: float = 500_000

@router.post("/api/backtest/run")
async def run_backtest(req: BacktestReq):
    df = await fetch_daily(req.symbol, req.exchange, req.days)
    if df is None or len(df)<90:
        raise HTTPException(400, f"Insufficient data for {req.symbol}. Need 90+ trading days.")
    bt  = Backtester(req.starting_capital)
    res = bt.run(req.symbol, df)
    if "error" in res:
        raise HTTPException(400, res["error"])
    rid = f"{req.symbol}_{req.days}d"
    _results[rid] = res
    summary = {k:v for k,v in res.items() if k not in ("equity_curve","trades")}
    summary["result_id"] = rid
    return summary

@router.get("/api/backtest/{result_id}/trades")
async def backtest_trades(result_id: str):
    if result_id not in _results: raise HTTPException(404,"Result not found")
    return {"trades": _results[result_id].get("trades",[])}

@router.get("/api/backtest/{result_id}/equity")
async def backtest_equity(result_id: str):
    if result_id not in _results: raise HTTPException(404,"Result not found")
    return {"equity_curve": _results[result_id].get("equity_curve",[])}

@router.get("/api/backtest/results/list")
async def list_results():
    return {"results":[{**{k:v for k,v in r.items() if k not in ("equity_curve","trades")},"result_id":rid}
                       for rid,r in _results.items()]}


# ── LIVE SCAN ─────────────────────────────────────────────────────────────────

@router.get("/api/scan/{symbol}")
async def scan_symbol(symbol: str, exchange: str = "NSE", days: int = 200):
    df = await fetch_daily(symbol, exchange, days)
    if df is None or len(df)<60:
        raise HTTPException(400, f"No data for {symbol}")
    orc = Orchestrator()
    result = orc.run(symbol, df)
    _scan_cache[symbol] = result
    return result

@router.get("/api/scan/bulk/nifty50")
async def scan_nifty50():
    """Scan top 10 Nifty50 stocks — returns signals and consensus for each."""
    from data import get_universe
    universe = get_universe()[:10]
    results = []
    for symbol, exchange in universe:
        df = await fetch_daily(symbol, exchange, 200)
        if df is None or len(df)<60: continue
        orc = Orchestrator()
        r   = orc.run(symbol, df)
        if r["signals"] or r["consensus"]:
            results.append(r)
    return {"scanned": len(universe), "with_signals": len(results), "results": results}

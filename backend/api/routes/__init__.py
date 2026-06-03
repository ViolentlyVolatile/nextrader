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
    # Store OHLCV for candlestick chart
    res["ohlcv"] = [{"i":i,"date":str(df.index[i].date()),
                     "open":round(float(df["open"].iloc[i]),2),
                     "high":round(float(df["high"].iloc[i]),2),
                     "low":round(float(df["low"].iloc[i]),2),
                     "close":round(float(df["close"].iloc[i]),2),
                     "volume":int(df["volume"].iloc[i])}
                    for i in range(len(df))]
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


@router.get("/api/backtest/{result_id}/ohlcv")
async def backtest_ohlcv(result_id: str):
    """Return OHLCV data used in the backtest for charting."""
    if result_id not in _results: raise HTTPException(404,"Result not found")
    return {"ohlcv": _results[result_id].get("ohlcv", [])}


@router.get("/api/backtest/{result_id}/ohlcv")
async def backtest_ohlcv(result_id: str):
    if result_id not in _results: raise HTTPException(404,"Result not found")
    return {"ohlcv": _results[result_id].get("ohlcv",[])}


# ── NSE Browser Data Ingestion ────────────────────────────────────────────────
# Receives OHLCV data POSTed from browser bookmarklet

from pydantic import BaseModel as _BM

class IngestRequest(_BM):
    symbol:   str
    exchange: str = "NSE"
    data:     list[dict]   # raw NSE API response rows

@router.post("/api/data/ingest")
async def ingest_data(req: IngestRequest):
    """Accept OHLCV data sent from browser. Saves to data/csv/{symbol}.json"""
    import os, json as _json
    from data import _load_sample_cache
    
    sym = req.symbol.upper()
    rows = []
    for r in req.data:
        try:
            rows.append({
                "date":   r.get("CH_TIMESTAMP","")[:10],
                "open":   float(r.get("CH_OPENING_PRICE", r.get("open", 0))),
                "high":   float(r.get("CH_TRADE_HIGH_PRICE", r.get("high", 0))),
                "low":    float(r.get("CH_TRADE_LOW_PRICE", r.get("low", 0))),
                "close":  float(r.get("CH_CLOSING_PRICE", r.get("close", 0))),
                "volume": int(r.get("CH_TOT_TRADED_QTY", r.get("volume", 0))),
            })
        except: pass

    if not rows:
        return {"error": "No valid rows parsed", "received": len(req.data)}

    rows.sort(key=lambda x: x["date"])

    # Save into sample_data cache so fetch_daily picks it up
    cache = _load_sample_cache()
    cache[sym] = rows

    # Also persist to disk
    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               '..', '..', 'data', 'sample_data.json')
    sample_path = os.path.normpath(sample_path)
    with open(sample_path, 'w') as f:
        _json.dump(cache, f)

    return {"status": "ok", "symbol": sym, "rows": len(rows), 
            "from": rows[0]["date"], "to": rows[-1]["date"]}


@router.get("/api/data/symbols")
async def list_symbols():
    """List symbols available in local data store"""
    from data import _load_sample_cache
    cache = _load_sample_cache()
    return {"symbols": [{"symbol": k, "bars": len(v), 
                          "from": v[0]["date"], "to": v[-1]["date"]}
                         for k,v in cache.items()]}

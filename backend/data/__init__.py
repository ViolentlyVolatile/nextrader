import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# ── UNIVERSE ─────────────────────────────────────────────────────────────────

NIFTY50 = [
    ("RELIANCE","NSE"),("TCS","NSE"),("HDFCBANK","NSE"),("INFY","NSE"),("ICICIBANK","NSE"),
    ("HINDUNILVR","NSE"),("ITC","NSE"),("SBIN","NSE"),("BAJFINANCE","NSE"),("BHARTIARTL","NSE"),
    ("KOTAKBANK","NSE"),("LT","NSE"),("HCLTECH","NSE"),("AXISBANK","NSE"),("ASIANPAINT","NSE"),
    ("MARUTI","NSE"),("WIPRO","NSE"),("TATAMOTORS","NSE"),("SUNPHARMA","NSE"),("TITAN","NSE"),
    ("NTPC","NSE"),("TECHM","NSE"),("JSWSTEEL","NSE"),("TATASTEEL","NSE"),("ONGC","NSE"),
    ("COALINDIA","NSE"),("ADANIENT","NSE"),("ADANIPORTS","NSE"),("BAJAJFINSV","NSE"),("CIPLA","NSE"),
]

# ── SAMPLE DATA (fallback when Yahoo Finance is not accessible) ───────────────

_SAMPLE_PATH = os.path.join(os.path.dirname(__file__), 'sample_data.json')
_sample_cache: dict = {}

def _load_sample(symbol: str) -> pd.DataFrame | None:
    global _sample_cache
    if not _sample_cache and os.path.exists(_SAMPLE_PATH):
        with open(_SAMPLE_PATH) as f:
            _sample_cache = json.load(f)
    if symbol.upper() not in _sample_cache:
        return None
    records = _sample_cache[symbol.upper()]
    df = pd.DataFrame(records)
    df.index = pd.to_datetime(df['date'])
    df = df.drop(columns=['date'])
    return df.sort_index()

# ── FETCHER ───────────────────────────────────────────────────────────────────

def _yf_ticker(symbol: str, exchange: str = "NSE") -> str:
    return f"{symbol}.{'NS' if exchange == 'NSE' else 'BO'}"

async def fetch_daily(symbol: str, exchange: str = "NSE", days: int = 365) -> pd.DataFrame | None:
    # 1. Try yfinance (works when running locally on your machine)
    try:
        end   = datetime.now()
        start = end - timedelta(days=days)
        df    = yf.Ticker(_yf_ticker(symbol, exchange)).history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval="1d")
        if df is not None and len(df) >= 90:
            df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
            df = df[["open","high","low","close","volume"]].dropna()
            df = df[df["volume"] > 0]
            df = df[df["close"].pct_change().abs().fillna(0) < 0.20]
            df.index = pd.to_datetime(df.index).tz_localize(None)
            print(f"[Data] {symbol}: {len(df)} bars from yfinance")
            return df.sort_index()
    except Exception as e:
        pass  # Fall through to sample data

    # 2. Fallback: bundled sample data (for demo / sandboxed environments)
    df = _load_sample(symbol)
    if df is not None:
        # Use tail(days) — sample data may predate today so date-based slicing undershoots
        n_bars = min(days, len(df))
        df = df.tail(n_bars)
        print(f"[Data] {symbol}: {len(df)} bars from sample data (yfinance unavailable)")
        return df

    print(f"[Data] {symbol}: no data available")
    return None

def get_universe() -> list[tuple[str, str]]:
    return NIFTY50

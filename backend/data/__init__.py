import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

NIFTY50 = [
    ("RELIANCE","NSE"),("TCS","NSE"),("HDFCBANK","NSE"),("INFY","NSE"),("ICICIBANK","NSE"),
    ("HINDUNILVR","NSE"),("ITC","NSE"),("SBIN","NSE"),("BAJFINANCE","NSE"),("BHARTIARTL","NSE"),
    ("KOTAKBANK","NSE"),("LT","NSE"),("HCLTECH","NSE"),("AXISBANK","NSE"),("ASIANPAINT","NSE"),
    ("MARUTI","NSE"),("WIPRO","NSE"),("TATAMOTORS","NSE"),("SUNPHARMA","NSE"),("TITAN","NSE"),
    ("NTPC","NSE"),("TECHM","NSE"),("JSWSTEEL","NSE"),("TATASTEEL","NSE"),("ONGC","NSE"),
    ("COALINDIA","NSE"),("ADANIENT","NSE"),("ADANIPORTS","NSE"),("BAJAJFINSV","NSE"),("CIPLA","NSE"),
]

_SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_data.json')
_sample_cache: dict = {}

# ── Auto-generate sample data if missing ─────────────────────────────────────

def _generate_sample_data():
    """Generate realistic NSE-like OHLCV data for 15 stocks. Called automatically if sample_data.json missing."""
    print("[Data] Generating sample_data.json (one-time setup)...")
    np.random.seed(42)
    STOCKS = {
        'RELIANCE':2800,'TCS':3500,'HDFCBANK':1650,'INFY':1450,'ICICIBANK':1100,
        'SBIN':750,'BAJFINANCE':6500,'AXISBANK':1020,'ITC':450,'WIPRO':470,
        'MARUTI':10800,'TATAMOTORS':850,'KOTAKBANK':1800,'LT':3200,'ADANIENT':2400,
    }

    def gen(symbol, base_price, n=750):
        np.random.seed(abs(hash(symbol)) % 2**31)
        closes = [float(base_price)]
        regime_len = n // 6
        regimes = []
        for _ in range(6):
            r = np.random.choice(['trend_up','trend_down','range','volatile'], p=[0.35,0.25,0.25,0.15])
            regimes.extend([r]*regime_len)
        regimes.extend(['range']*(n - len(regimes)))
        for i in range(1, n):
            r = regimes[i]
            if r == 'trend_up':    drift, vol = 0.0015, 0.012
            elif r == 'trend_down': drift, vol = -0.001, 0.013
            elif r == 'range':
                drift = -0.0003*(closes[-1]-base_price)/base_price; vol = 0.010
            else:
                drift = np.random.normal(0, 0.002); vol = 0.025
            ret = np.random.choice([-1,1])*np.random.uniform(0.03,0.07) if np.random.random()<0.03 \
                  else np.random.normal(drift, vol)
            closes.append(max(closes[-1]*(1+ret), base_price*0.3))
        closes = np.array(closes)
        atr    = closes * np.random.uniform(0.012, 0.022, n)
        highs  = closes + atr * np.random.uniform(0.4, 0.9, n)
        lows   = closes - atr * np.random.uniform(0.4, 0.9, n)
        opens  = np.clip(closes*(1+np.random.normal(0,0.006,n)), lows, highs)
        vols   = (np.random.randint(3_000_000,15_000_000)*np.abs(np.random.lognormal(0,0.6,n))).astype(int)
        start  = datetime(2022, 1, 3)
        dates, d = [], start
        while len(dates) < n:
            if d.weekday() < 5: dates.append(d.strftime('%Y-%m-%d'))
            d += timedelta(days=1)
        return [{'date':dates[i],'open':round(float(opens[i]),2),'high':round(float(highs[i]),2),
                 'low':round(float(lows[i]),2),'close':round(float(closes[i]),2),'volume':int(vols[i])}
                for i in range(n)]

    data = {sym: gen(sym, price) for sym, price in STOCKS.items()}
    os.makedirs(os.path.dirname(_SAMPLE_PATH), exist_ok=True)
    with open(_SAMPLE_PATH, 'w') as f:
        json.dump(data, f)
    print(f"[Data] sample_data.json created — {len(data)} stocks × 750 bars")
    return data


def _load_sample_cache():
    global _sample_cache
    if _sample_cache:
        return _sample_cache
    if not os.path.exists(_SAMPLE_PATH):
        _sample_cache = _generate_sample_data()
    else:
        with open(_SAMPLE_PATH) as f:
            _sample_cache = json.load(f)
    return _sample_cache


def _load_sample(symbol: str) -> pd.DataFrame | None:
    cache = _load_sample_cache()
    records = cache.get(symbol.upper())
    if not records:
        return None
    df = pd.DataFrame(records)
    df.index = pd.to_datetime(df['date'])
    return df.drop(columns=['date']).sort_index()


# ── Data fetcher ──────────────────────────────────────────────────────────────

def _yf_ticker(symbol: str, exchange: str = "NSE") -> str:
    return f"{symbol}.{'NS' if exchange == 'NSE' else 'BO'}"


async def fetch_daily(symbol: str, exchange: str = "NSE", days: int = 365) -> pd.DataFrame | None:
    # 1. Try yfinance (works on real internet)
    try:
        import logging; logging.getLogger('yfinance').setLevel(logging.CRITICAL)
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
    except Exception:
        pass

    # 2. Fallback: auto-generated sample data
    df = _load_sample(symbol)
    if df is not None:
        n = min(days, len(df))
        df = df.tail(n)
        print(f"[Data] {symbol}: {len(df)} bars from sample data")
        return df

    print(f"[Data] {symbol}: no data available")
    return None


def get_universe() -> list[tuple[str, str]]:
    return NIFTY50

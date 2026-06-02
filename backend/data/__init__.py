import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

NIFTY50 = [
    ("RELIANCE","NSE"),("TCS","NSE"),("HDFCBANK","NSE"),("INFY","NSE"),("ICICIBANK","NSE"),
    ("HINDUNILVR","NSE"),("ITC","NSE"),("SBIN","NSE"),("BAJFINANCE","NSE"),("BHARTIARTL","NSE"),
    ("KOTAKBANK","NSE"),("LT","NSE"),("HCLTECH","NSE"),("AXISBANK","NSE"),("ASIANPAINT","NSE"),
    ("MARUTI","NSE"),("WIPRO","NSE"),("TATAMOTORS","NSE"),("SUNPHARMA","NSE"),("TITAN","NSE"),
    ("NTPC","NSE"),("TECHM","NSE"),("JSWSTEEL","NSE"),("TATASTEEL","NSE"),("ONGC","NSE"),
    ("COALINDIA","NSE"),("ADANIENT","NSE"),("ADANIPORTS","NSE"),("BAJAJFINSV","NSE"),("CIPLA","NSE"),
]

def _yf(symbol: str, exchange: str = "NSE") -> str:
    return f"{symbol}.{'NS' if exchange=='NSE' else 'BO'}"

async def fetch_daily(symbol: str, exchange: str = "NSE", days: int = 365) -> pd.DataFrame | None:
    try:
        end   = datetime.now()
        start = end - timedelta(days=days)
        df    = yf.Ticker(_yf(symbol,exchange)).history(
            start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval="1d")
        if df is None or len(df)==0: return None
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df = df[["open","high","low","close","volume"]].dropna()
        df = df[df["volume"]>0]
        # Remove price spikes > 20%
        df = df[df["close"].pct_change().abs().fillna(0) < 0.20]
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    except Exception as e:
        print(f"[Data] {symbol}: {e}")
        return None

def get_universe() -> list[tuple[str,str]]:
    return NIFTY50

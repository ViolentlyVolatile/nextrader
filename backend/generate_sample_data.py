"""
Run this once to generate sample data for backtesting when yfinance is unavailable.
Usage: python generate_sample_data.py
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

np.random.seed(42)

STOCKS = {
    'RELIANCE':2800,'TCS':3500,'HDFCBANK':1650,'INFY':1450,'ICICIBANK':1100,
    'SBIN':750,'BAJFINANCE':6500,'AXISBANK':1020,'ITC':450,'WIPRO':470,
    'MARUTI':10800,'TATAMOTORS':850,'KOTAKBANK':1800,'LT':3200,'ADANIENT':2400,
}

def gen_stock(symbol, base_price, n=750):
    np.random.seed(abs(hash(symbol)) % 2**31)
    closes = [float(base_price)]
    regime_len = n // 6
    regimes = []
    for _ in range(6):
        r = np.random.choice(['trend_up','trend_down','range','volatile'], p=[0.35,0.25,0.25,0.15])
        regimes.extend([r]*regime_len)
    regimes.extend(['range']*(n-len(regimes)))

    for i in range(1, n):
        r = regimes[i]
        if r == 'trend_up':    drift, vol = 0.0015, 0.012
        elif r == 'trend_down': drift, vol = -0.001, 0.013
        elif r == 'range':
            drift = -0.0003*(closes[-1]-base_price)/base_price; vol = 0.010
        else:
            drift = np.random.normal(0, 0.002); vol = 0.025
        if np.random.random() < 0.03:
            ret = np.random.choice([-1,1])*np.random.uniform(0.03, 0.07)
        else:
            ret = np.random.normal(drift, vol)
        closes.append(max(closes[-1]*(1+ret), base_price*0.3))

    closes = np.array(closes)
    atr    = closes * np.random.uniform(0.012, 0.022, n)
    highs  = closes + atr * np.random.uniform(0.4, 0.9, n)
    lows   = closes - atr * np.random.uniform(0.4, 0.9, n)
    opens  = np.clip(closes*(1+np.random.normal(0,0.006,n)), lows, highs)
    base_vol = np.random.randint(3_000_000, 15_000_000)
    volumes  = (base_vol*np.abs(np.random.lognormal(0, 0.6, n))).astype(int)

    start = datetime(2022, 1, 3)
    dates, d = [], start
    while len(dates) < n:
        if d.weekday() < 5: dates.append(d.strftime('%Y-%m-%d'))
        d += timedelta(days=1)

    return pd.DataFrame({'date':dates,'open':np.round(opens,2),'high':np.round(highs,2),
                         'low':np.round(lows,2),'close':np.round(closes,2),'volume':volumes})

out_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_data.json')
data = {}
for sym, price in STOCKS.items():
    df = gen_stock(sym, price)
    data[sym] = df.to_dict(orient='records')
    print(f"  {sym}: {len(df)} bars  ₹{price} → ₹{df['close'].iloc[-1]:.0f}")

with open(out_path, 'w') as f:
    json.dump(data, f)

print(f"\n✅ Sample data saved to {out_path}")
print(f"   {len(data)} stocks × {len(list(data.values())[0])} bars each")

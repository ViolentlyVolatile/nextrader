import pandas as pd
import numpy as np

# ── MOMENTUM ────────────────────────────────────────────────────────────────

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    ag = gain.ewm(com=period-1, min_periods=period).mean()
    al = loss.ewm(com=period-1, min_periods=period).mean()
    return 100 - (100 / (1 + ag / al.replace(0, np.nan)))

def macd(df, fast=12, slow=26, signal=9):
    ef = df["close"].ewm(span=fast, adjust=False).mean()
    es = df["close"].ewm(span=slow, adjust=False).mean()
    line = ef - es
    sig  = line.ewm(span=signal, adjust=False).mean()
    return line, sig, line - sig

def stochastic(df, k=14, d=3, smooth=3):
    lo = df["low"].rolling(k).min()
    hi = df["high"].rolling(k).max()
    ks = (100*(df["close"]-lo)/(hi-lo).replace(0,np.nan)).rolling(smooth).mean()
    return ks, ks.rolling(d).mean()

def roc(df, period=10):
    return df["close"].pct_change(period)*100

# ── TREND ────────────────────────────────────────────────────────────────────

def ema(df, period=21, col="close"):
    return df[col].ewm(span=period, adjust=False).mean()

def sma(df, period=20):
    return df["close"].rolling(period).mean()

def adx(df, period=14):
    h,l,c = df["high"], df["low"], df["close"]
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    dmp = ((h-h.shift())>(l.shift()-l)).astype(float)*(h-h.shift()).clip(lower=0)
    dmm = ((l.shift()-l)>(h-h.shift())).astype(float)*(l.shift()-l).clip(lower=0)
    atr_ = tr.ewm(span=period,adjust=False).mean()
    dip = 100*dmp.ewm(span=period,adjust=False).mean()/atr_.replace(0,np.nan)
    dim = 100*dmm.ewm(span=period,adjust=False).mean()/atr_.replace(0,np.nan)
    dx  = 100*(dip-dim).abs()/(dip+dim).replace(0,np.nan)
    return dx.ewm(span=period,adjust=False).mean(), dip, dim

def supertrend(df, period=7, mult=3.0):
    h,l,c = df["high"], df["low"], df["close"]
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    atr_ = tr.ewm(span=period,adjust=False).mean()
    hl2  = (h+l)/2
    up   = hl2 + mult*atr_
    dn   = hl2 - mult*atr_
    fu,fd = up.copy(), dn.copy()
    for i in range(1,len(df)):
        fu.iloc[i] = min(up.iloc[i],fu.iloc[i-1]) if c.iloc[i-1]>fu.iloc[i-1] else up.iloc[i]
        fd.iloc[i] = max(dn.iloc[i],fd.iloc[i-1]) if c.iloc[i-1]<fd.iloc[i-1] else dn.iloc[i]
    st  = pd.Series(index=df.index, dtype=float)
    dir_= pd.Series(0, index=df.index)
    for i in range(1,len(df)):
        if c.iloc[i]>fu.iloc[i-1]:   dir_.iloc[i]=1
        elif c.iloc[i]<fd.iloc[i-1]: dir_.iloc[i]=-1
        else:                          dir_.iloc[i]=dir_.iloc[i-1]
        st.iloc[i] = fd.iloc[i] if dir_.iloc[i]==1 else fu.iloc[i]
    return st, dir_

def ichimoku(df):
    h,l,c = df["high"],df["low"],df["close"]
    ten = (h.rolling(9).max()+l.rolling(9).min())/2
    kij = (h.rolling(26).max()+l.rolling(26).min())/2
    sa  = ((ten+kij)/2).shift(26)
    sb  = ((h.rolling(52).max()+l.rolling(52).min())/2).shift(26)
    return {"tenkan":ten,"kijun":kij,"senkou_a":sa,"senkou_b":sb}

def parabolic_sar(df, step=0.02, max_step=0.2):
    hi,lo = df["high"].values, df["low"].values
    n = len(df); sar=np.zeros(n); ep=lo[0]; af=step; up=True; sar[0]=hi[0]
    for i in range(1,n):
        sar[i]=sar[i-1]+af*(ep-sar[i-1])
        if up:
            if lo[i]<sar[i]: up=False;sar[i]=ep;ep=lo[i];af=step
            else:
                if hi[i]>ep: ep=hi[i];af=min(af+step,max_step)
                sar[i]=min(sar[i],lo[max(0,i-1)],lo[i])
        else:
            if hi[i]>sar[i]: up=True;sar[i]=ep;ep=hi[i];af=step
            else:
                if lo[i]<ep: ep=lo[i];af=min(af+step,max_step)
                sar[i]=max(sar[i],hi[max(0,i-1)],hi[i])
    return pd.Series(sar, index=df.index)

# ── VOLATILITY ───────────────────────────────────────────────────────────────

def bollinger(df, period=20, std=2.0):
    mid = df["close"].rolling(period).mean()
    s   = df["close"].rolling(period).std()
    return mid+std*s, mid, mid-std*s

def atr(df, period=14):
    h,l,c = df["high"],df["low"],df["close"]
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(span=period,adjust=False).mean()

def bb_squeeze(df, bb_p=20, kc_p=20, kc_m=1.5):
    ub,_,lb = bollinger(df,bb_p)
    mk = df["close"].rolling(kc_p).mean()
    ak = atr(df,kc_p)
    return ((ub<mk+kc_m*ak)&(lb>mk-kc_m*ak)).astype(int)

# ── VOLUME ───────────────────────────────────────────────────────────────────

def vwap(df):
    tp = (df["high"]+df["low"]+df["close"])/3
    return (tp*df["volume"]).cumsum()/df["volume"].cumsum().replace(0,np.nan)

def vol_ratio(df, period=20):
    return df["volume"]/df["volume"].rolling(period).mean().replace(0,np.nan)

def volume_poc(df, bins=50):
    pr = np.linspace(df["low"].min(), df["high"].max(), bins)
    va = np.zeros(bins-1)
    for i in range(len(df)):
        for j in range(bins-1):
            if pr[j]<=df["close"].iloc[i]<pr[j+1]:
                va[j]+=df["volume"].iloc[i]
    idx=np.argmax(va)
    return (pr[idx]+pr[idx+1])/2

# ── PATTERNS ──────────────────────────────────────────────────────────────────

def bull_engulf(df):
    return ((df["open"].shift(1)>df["close"].shift(1)) &
            (df["close"]>df["open"]) &
            (df["open"]<df["close"].shift(1)) &
            (df["close"]>df["open"].shift(1))).astype(int)

def bear_engulf(df):
    return ((df["close"].shift(1)>df["open"].shift(1)) &
            (df["open"]>df["close"]) &
            (df["open"]>df["close"].shift(1)) &
            (df["close"]<df["open"].shift(1))).astype(int)

def pin_bull(df, ratio=2.0):
    body = (df["close"]-df["open"]).abs()
    lw   = df[["open","close"]].min(axis=1)-df["low"]
    uw   = df["high"]-df[["open","close"]].max(axis=1)
    return ((lw>ratio*body.replace(0,0.001))&(uw<0.5*lw)).astype(int)

def pin_bear(df, ratio=2.0):
    body = (df["close"]-df["open"]).abs()
    uw   = df["high"]-df[["open","close"]].max(axis=1)
    lw   = df[["open","close"]].min(axis=1)-df["low"]
    return ((uw>ratio*body.replace(0,0.001))&(lw<0.5*uw)).astype(int)

def inside_bar(df):
    return ((df["high"]<df["high"].shift(1))&(df["low"]>df["low"].shift(1))).astype(int)

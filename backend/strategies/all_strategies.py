"""All 12 strategies — each ~30 lines. Signal fires only if .passes() is True."""
import pandas as pd
import numpy as np
from typing import Optional
from strategies.base import BaseStrategy, Signal
import indicators as ind


class MomentumRSI(BaseStrategy):
    name = "MomentumRSI"
    default_params = {"rsi_period":14,"rsi_os":35,"rsi_ob":65,"roc_period":10}

    def generate(self, df, symbol):
        if len(df)<50: return None
        r=ind.rsi(df,self.params["rsi_period"]).iloc[-1]
        roc=ind.roc(df,self.params["roc_period"]).iloc[-1]
        vr=ind.vol_ratio(df).iloc[-1]
        if pd.isna(r) or pd.isna(roc): return None
        if r<self.params["rsi_os"] and roc>0:   dir_="BUY";  ia=min((self.params["rsi_os"]-r)/self.params["rsi_os"]+0.1,1.0)
        elif r>self.params["rsi_ob"] and roc<0: dir_="SELL"; ia=min((r-self.params["rsi_ob"])/(100-self.params["rsi_ob"])+0.1,1.0)
        else: return None
        p=df["close"].iloc[-1]; a=self._atr(df)
        sl=p-1.5*a if dir_=="BUY" else p+1.5*a; tgt=p+3*a if dir_=="BUY" else p-3*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=min(float(vr)/2,1.0) if not pd.isna(vr) else 0.5,
                 regime_fit=0.6,historical_win_rate=self._win_rate,suggested_entry=round(p,2),
                 suggested_sl=round(sl,2),suggested_target=round(tgt,2),strategy_name=self.name,
                 signal_data={"rsi":round(r,2),"roc":round(roc,2)})
        return s if s.passes() else None


class VWAPReversion(BaseStrategy):
    name = "VWAPReversion"
    default_params = {"dev_threshold":0.02}

    def generate(self, df, symbol):
        if len(df)<30: return None
        v=ind.vwap(df).iloc[-1]; p=df["close"].iloc[-1]
        dev=(p-v)/v
        if abs(dev)<self.params["dev_threshold"]: return None
        dir_="BUY" if dev<0 else "SELL"
        a=self._atr(df); ia=min(abs(dev)/0.05,1.0)
        sl=p-a if dir_=="BUY" else p+a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="5m",indicator_agreement=float(ia),
                 volume_confirmation=0.65,regime_fit=0.55,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(v,2),
                 strategy_name=self.name,signal_data={"vwap":round(v,2),"dev_pct":round(dev*100,2)})
        return s if s.passes() else None


class EMACrossover(BaseStrategy):
    name = "EMACrossover"
    default_params = {"fast":9,"slow":21}

    def generate(self, df, symbol):
        if len(df)<50: return None
        f=ind.ema(df,self.params["fast"]); sl_=ind.ema(df,self.params["slow"])
        vr=ind.vol_ratio(df).iloc[-1]
        cu=f.iloc[-2]<=sl_.iloc[-2] and f.iloc[-1]>sl_.iloc[-1]
        cd=f.iloc[-2]>=sl_.iloc[-2] and f.iloc[-1]<sl_.iloc[-1]
        if not cu and not cd: return None
        dir_="BUY" if cu else "SELL"; p=df["close"].iloc[-1]; a=self._atr(df)
        sep=abs(f.iloc[-1]-sl_.iloc[-1])/p; ia=min(sep*100,1.0)
        tgt_=p+2.5*a if dir_=="BUY" else p-2.5*a; sl=p-1.5*a if dir_=="BUY" else p+1.5*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=min(float(vr)/2,1.0) if not pd.isna(vr) else 0.5,
                 regime_fit=0.65,historical_win_rate=self._win_rate,suggested_entry=round(p,2),
                 suggested_sl=round(sl,2),suggested_target=round(tgt_,2),strategy_name=self.name,
                 signal_data={"fast_ema":round(f.iloc[-1],2),"slow_ema":round(sl_.iloc[-1],2)})
        return s if s.passes() else None


class SupertrendADX(BaseStrategy):
    name = "SupertrendADX"
    default_params = {"st_p":7,"st_m":3.0,"adx_p":14,"adx_th":25}

    def generate(self, df, symbol):
        if len(df)<60: return None
        st,d=ind.supertrend(df,self.params["st_p"],self.params["st_m"])
        adx_,dip,dim=ind.adx(df,self.params["adx_p"])
        if pd.isna(adx_.iloc[-1]) or adx_.iloc[-1]<self.params["adx_th"]: return None
        if d.iloc[-1]==d.iloc[-2]: return None
        dir_="BUY" if d.iloc[-1]==1 else "SELL"; p=df["close"].iloc[-1]; a=self._atr(df)
        ia=min((adx_.iloc[-1]-25)/50+0.3,1.0)
        sl=p-1.5*a if dir_=="BUY" else p+1.5*a; tgt=p+3*a if dir_=="BUY" else p-3*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.6,regime_fit=0.75,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"adx":round(adx_.iloc[-1],2)})
        return s if s.passes() else None


class BollingerSqueeze(BaseStrategy):
    name = "BollingerSqueeze"
    default_params = {"bb_p":20,"kc_p":20}

    def generate(self, df, symbol):
        if len(df)<50: return None
        sq=ind.bb_squeeze(df,self.params["bb_p"],self.params["kc_p"])
        if not (sq.iloc[-2]==1 and sq.iloc[-1]==0): return None
        r=ind.rsi(df).iloc[-1]; ub,_,lb=ind.bollinger(df,self.params["bb_p"])
        p=df["close"].iloc[-1]; a=self._atr(df)
        dir_="BUY" if p>ub.iloc[-2] or r>55 else "SELL"
        sq_dur=int(sq[::-1].cumprod().sum()); ia=min(0.5+sq_dur*0.05,1.0)
        sl=p-2*a if dir_=="BUY" else p+2*a; tgt=p+4*a if dir_=="BUY" else p-4*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.6,regime_fit=0.6,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"squeeze_bars":sq_dur,"rsi":round(r,2)})
        return s if s.passes() else None


class PriceAction(BaseStrategy):
    name = "PriceAction"
    default_params = {}

    def generate(self, df, symbol):
        if len(df)<30: return None
        bc=int(ind.bull_engulf(df).iloc[-1])+int(ind.pin_bull(df).iloc[-1])
        brc=int(ind.bear_engulf(df).iloc[-1])+int(ind.pin_bear(df).iloc[-1])
        if bc==0 and brc==0: return None
        dir_="BUY" if bc>=brc else "SELL"; ia=max(bc,brc)/2.0
        p=df["close"].iloc[-1]; a=self._atr(df)
        sl=p-1.5*a if dir_=="BUY" else p+1.5*a; tgt=p+3*a if dir_=="BUY" else p-3*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=min(ia,1.0),
                 volume_confirmation=0.6,regime_fit=0.6,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"bull":bc,"bear":brc})
        return s if s.passes() else None


class OpeningRangeBreakout(BaseStrategy):
    name = "ORB"
    default_params = {"orb_bars":3,"vol_mult":1.5}

    def generate(self, df, symbol):
        if len(df)<10: return None
        oh=df["high"].iloc[:self.params["orb_bars"]].max()
        ol=df["low"].iloc[:self.params["orb_bars"]].min()
        p=df["close"].iloc[-1]; vr=ind.vol_ratio(df).iloc[-1]
        if p>oh and vr>self.params["vol_mult"]: dir_="BUY"
        elif p<ol and vr>self.params["vol_mult"]: dir_="SELL"
        else: return None
        orb=oh-ol; sl=(oh-0.5*orb) if dir_=="BUY" else (ol+0.5*orb)
        tgt=p+2*orb if dir_=="BUY" else p-2*orb; ia=min((vr-1)/2,1.0)
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="15m",indicator_agreement=float(ia),
                 volume_confirmation=min(float(vr)/3,1.0),regime_fit=0.65,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"orb_high":round(oh,2),"orb_low":round(ol,2)})
        return s if s.passes() else None


class MACDDivergence(BaseStrategy):
    name = "MACDDivergence"
    default_params = {"fast":12,"slow":26,"signal":9,"lb":10}

    def generate(self, df, symbol):
        if len(df)<60: return None
        _,__,hist=ind.macd(df,self.params["fast"],self.params["slow"],self.params["signal"])
        lb=self.params["lb"]
        ps=df["close"].iloc[-lb:].diff().mean(); hs=hist.iloc[-lb:].diff().mean()
        bull=ps<0 and hs>0 and hist.iloc[-1]<0
        bear=ps>0 and hs<0 and hist.iloc[-1]>0
        if not bull and not bear: return None
        dir_="BUY" if bull else "SELL"; p=df["close"].iloc[-1]; a=self._atr(df)
        ia=min(abs(hs)/(abs(ps)+0.001)*0.5,1.0)
        sl=p-2*a if dir_=="BUY" else p+2*a; tgt=p+3*a if dir_=="BUY" else p-3*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.55,regime_fit=0.6,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"hist":round(hist.iloc[-1],4)})
        return s if s.passes() else None


class StochasticSwing(BaseStrategy):
    name = "StochasticSwing"
    default_params = {"k":14,"d":3,"sm":3,"os":20,"ob":80}

    def generate(self, df, symbol):
        if len(df)<50: return None
        ks,ds=ind.stochastic(df,self.params["k"],self.params["d"],self.params["sm"])
        cu=ks.iloc[-2]<=ds.iloc[-2] and ks.iloc[-1]>ds.iloc[-1] and ks.iloc[-1]<self.params["os"]+15
        cd=ks.iloc[-2]>=ds.iloc[-2] and ks.iloc[-1]<ds.iloc[-1] and ks.iloc[-1]>self.params["ob"]-15
        if not cu and not cd: return None
        dir_="BUY" if cu else "SELL"; p=df["close"].iloc[-1]; a=self._atr(df)
        ia=min(max((self.params["os"]-ks.iloc[-1])/self.params["os"] if cu else (ks.iloc[-1]-self.params["ob"])/(100-self.params["ob"]),0.3),1.0)
        sl=p-1.5*a if dir_=="BUY" else p+1.5*a; tgt=p+2.5*a if dir_=="BUY" else p-2.5*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.55,regime_fit=0.55,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"k":round(ks.iloc[-1],2),"d":round(ds.iloc[-1],2)})
        return s if s.passes() else None


class IchimokuCloud(BaseStrategy):
    name = "Ichimoku"
    default_params = {}

    def generate(self, df, symbol):
        if len(df)<80: return None
        ic=ind.ichimoku(df)
        t,k,sa,sb=ic["tenkan"].iloc[-1],ic["kijun"].iloc[-1],ic["senkou_a"].iloc[-1],ic["senkou_b"].iloc[-1]
        if any(pd.isna([t,k,sa,sb])): return None
        ct=max(sa,sb); cb=min(sa,sb); p=df["close"].iloc[-1]
        tku=ic["tenkan"].iloc[-2]<=ic["kijun"].iloc[-2] and t>k
        tkd=ic["tenkan"].iloc[-2]>=ic["kijun"].iloc[-2] and t<k
        if tku and p>ct: dir_="BUY"
        elif tkd and p<cb: dir_="SELL"
        else: return None
        a=self._atr(df); th=abs(sa-sb)/p; ia=min(0.6+th*10,1.0)
        sl=p-2*a if dir_=="BUY" else p+2*a; tgt=p+3.5*a if dir_=="BUY" else p-3.5*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.6,regime_fit=0.7,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"tenkan":round(t,2),"kijun":round(k,2)})
        return s if s.passes() else None


class ParabolicSAR(BaseStrategy):
    name = "ParabolicSAR"
    default_params = {"step":0.02,"max":0.2,"ema_p":50}

    def generate(self, df, symbol):
        if len(df)<60: return None
        sar=ind.parabolic_sar(df,self.params["step"],self.params["max"])
        em=ind.ema(df,self.params["ema_p"]); p=df["close"].iloc[-1]
        fu=sar.iloc[-2]>df["close"].iloc[-2] and sar.iloc[-1]<p
        fd=sar.iloc[-2]<df["close"].iloc[-2] and sar.iloc[-1]>p
        if not fu and not fd: return None
        if fu and p<em.iloc[-1]: return None
        if fd and p>em.iloc[-1]: return None
        dir_="BUY" if fu else "SELL"; a=self._atr(df)
        ed=abs(p-em.iloc[-1])/p; ia=min(0.5+ed*20,1.0)
        sl=sar.iloc[-1]; tgt=p+2.5*a if dir_=="BUY" else p-2.5*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=0.6,regime_fit=0.65,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"sar":round(sar.iloc[-1],2),"ema":round(em.iloc[-1],2)})
        return s if s.passes() else None


class VolumePOC(BaseStrategy):
    name = "VolumePOC"
    default_params = {"lb":50,"bk_pct":0.005}

    def generate(self, df, symbol):
        if len(df)<60: return None
        poc=ind.volume_poc(df.iloc[-self.params["lb"]:])
        p=df["close"].iloc[-1]; pp=df["close"].iloc[-2]
        bu=pp<=poc*(1+self.params["bk_pct"]) and p>poc*(1+self.params["bk_pct"])
        bd=pp>=poc*(1-self.params["bk_pct"]) and p<poc*(1-self.params["bk_pct"])
        if not bu and not bd: return None
        dir_="BUY" if bu else "SELL"
        vr=ind.vol_ratio(df).iloc[-1]; a=self._atr(df)
        ia=min(float(vr)/2.5,1.0); sl=poc; tgt=p+2.5*a if dir_=="BUY" else p-2.5*a
        s=Signal(symbol,exchange="NSE",direction=dir_,timeframe="1d",indicator_agreement=float(ia),
                 volume_confirmation=min(float(vr)/2,1.0),regime_fit=0.6,historical_win_rate=self._win_rate,
                 suggested_entry=round(p,2),suggested_sl=round(sl,2),suggested_target=round(tgt,2),
                 strategy_name=self.name,signal_data={"poc":round(poc,2),"vol_ratio":round(float(vr),2)})
        return s if s.passes() else None


ALL_STRATEGIES = [
    MomentumRSI, VWAPReversion, EMACrossover, SupertrendADX,
    BollingerSqueeze, PriceAction, OpeningRangeBreakout, MACDDivergence,
    StochasticSwing, IchimokuCloud, ParabolicSAR, VolumePOC
]

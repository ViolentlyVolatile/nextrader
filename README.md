# NEXTRADER — Evolutionary Multi-Strategy Algo Trader

> Indian markets (NSE · BSE · F&O) · 12 parallel strategies · Confidence-scored signals · Consensus layer

## Phase 1 — Core Engine + Backtester + Dashboard

### Stack
- **Backend:** Python 3.11 · FastAPI · SQLite · pandas · numpy · yfinance
- **Frontend:** React 18 · Vite · Tailwind CSS v4 · Recharts

---

## Quick Start

### 1. Clone locally
```powershell
git clone https://github.com/ViolentlyVolatile/nextrader.git D:\CLAUDE_COWORK\nextrader
cd D:\CLAUDE_COWORK\nextrader
```

### 2. Backend
```powershell
cd backend
copy .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```
API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

### 3. Frontend
```powershell
cd frontend
npm install
npm run dev
```
Dashboard: http://localhost:5173

---

## The 12 Strategies

| # | Strategy | Type | Timeframe |
|---|---|---|---|
| 1 | MomentumRSI | Trend + Momentum | Daily |
| 2 | VWAPReversion | Mean Reversion | 5m |
| 3 | EMACrossover | Trend | Daily |
| 4 | SupertrendADX | Trend + Strength | Daily |
| 5 | BollingerSqueeze | Volatility Breakout | Daily |
| 6 | PriceAction | Pattern Recognition | Daily |
| 7 | ORB | Opening Range Breakout | 15m |
| 8 | MACDDivergence | Divergence | Daily |
| 9 | StochasticSwing | Oscillator Swing | Daily |
| 10 | Ichimoku | Cloud Breakout | Daily |
| 11 | ParabolicSAR | Trend Reversal | Daily |
| 12 | VolumePOC | Volume Profile | Daily |

## Confidence Score Formula
```
confidence = (
    indicator_agreement  × 0.35 +
    historical_win_rate  × 0.30 +
    volume_confirmation  × 0.20 +
    regime_fit           × 0.15
) × 100
```
Signal fires: confidence ≥ 55%  
Consensus trade: ≥2 strategies agree · avg confidence ≥ 60%

## Notes on Data
- **On your machine:** yfinance fetches real NSE/BSE data automatically
- **Demo/offline:** bundled `sample_data.json` (15 stocks × 750 bars) is used as fallback

## Roadmap
- **Phase 2:** Paper trading with live Zerodha Kite feed + WebSocket dashboard
- **Phase 3:** Genetic algorithm strategy optimizer + strategy graveyard
- **Phase 4:** Live order execution with hard safety gates

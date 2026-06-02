# NEXTRADER — Evolutionary Multi-Strategy Algo Trader

> Indian markets (NSE · BSE · F&O) · 12 parallel strategies · Confidence-scored signals · Consensus layer

## Phase 1 — Core Engine + Backtester + Dashboard

### Stack
- **Backend:** Python 3.11 · FastAPI · SQLite · pandas · numpy · yfinance
- **Frontend:** React 18 · Vite · Tailwind CSS v4 · Recharts

### Features
- 12 independent strategy agents running in parallel
- Confidence scoring (0–100%) per signal
- Consensus layer: trade only when ≥3 strategies agree at ≥65%
- Backtesting with Zerodha brokerage simulation (₹20 flat + STT + GST)
- Kelly Criterion position sizing (capped at 25%)
- Risk controls: 1% max risk/trade · 5 max positions · 3% daily loss limit → halt
- Live scanner: scan any NSE/BSE symbol or bulk scan Nifty50

---

## Quick Start

### 1. Backend

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload
```

API available at: http://localhost:8000
Swagger docs at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard at: http://localhost:5173

---

## Project Structure

```
nextrader/
├── backend/
│   ├── main.py              # FastAPI entrypoint
│   ├── config.py            # All constants (capital, risk, thresholds)
│   ├── database.py          # SQLAlchemy async setup
│   ├── models/              # Trade, Signal, StrategyStat ORM models
│   ├── indicators/          # All technical indicators (momentum/trend/vol/volume/patterns)
│   ├── strategies/          # All 12 strategies + base class
│   ├── engine/              # Orchestrator, consensus, regime, risk, brokerage
│   ├── backtester/          # Backtest engine, portfolio, metrics
│   ├── data/                # yfinance data fetcher, NSE universe
│   └── api/routes/          # All FastAPI routes
└── frontend/
    └── src/
        ├── pages/           # Dashboard, Backtest, Strategies, Scanner
        ├── components/      # Sidebar + layout
        └── api/client.js    # Axios API client
```

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

Signal fires: confidence ≥ 60%  
Consensus trade: ≥3 strategies agree · avg confidence ≥ 65%

---

## Roadmap

- **Phase 2:** Paper trading with live Zerodha Kite feed + WebSocket dashboard
- **Phase 3:** Genetic algorithm strategy optimizer + strategy graveyard
- **Phase 4:** Live order execution with hard safety gates

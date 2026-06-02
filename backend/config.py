import os
from dotenv import load_dotenv
load_dotenv()

STARTING_CAPITAL     = float(os.getenv("STARTING_CAPITAL", 500_000))
MAX_RISK_PCT         = 0.01
MAX_RISK             = STARTING_CAPITAL * MAX_RISK_PCT
MAX_POSITIONS        = 5
DAILY_LOSS_LIMIT     = STARTING_CAPITAL * 0.03
KELLY_CAP            = 0.25

# Signal thresholds — lower for backtesting exploration, raise for live
MIN_CONFIDENCE       = float(os.getenv("MIN_CONFIDENCE", 55.0))   # was 60
CONSENSUS_MIN_COUNT  = int(os.getenv("CONSENSUS_MIN_COUNT", 2))    # was 3
CONSENSUS_MIN_CONF   = float(os.getenv("CONSENSUS_MIN_CONF", 60.0))# was 65

# Brokerage (Zerodha)
BROKERAGE_PER_ORDER  = 20.0
STT_PCT              = 0.00025
EXCHANGE_PCT         = 0.0000335
GST_PCT              = 0.18

DATABASE_URL         = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nextrader.db")
KITE_API_KEY         = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET      = os.getenv("KITE_API_SECRET", "")

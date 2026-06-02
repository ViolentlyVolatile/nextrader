import os
from dotenv import load_dotenv
load_dotenv()

STARTING_CAPITAL     = float(os.getenv("STARTING_CAPITAL", 500_000))
MAX_RISK_PCT         = 0.01
MAX_RISK             = STARTING_CAPITAL * MAX_RISK_PCT
MAX_POSITIONS        = 5
DAILY_LOSS_LIMIT     = STARTING_CAPITAL * 0.03
KELLY_CAP            = 0.25
MIN_CONFIDENCE       = 60.0
CONSENSUS_MIN_COUNT  = 3
CONSENSUS_MIN_CONF   = 65.0
BROKERAGE_PER_ORDER  = 20.0
STT_PCT              = 0.00025
EXCHANGE_PCT         = 0.0000335
GST_PCT              = 0.18
DATABASE_URL         = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nextrader.db")
KITE_API_KEY         = os.getenv("KITE_API_KEY", "")
KITE_API_SECRET      = os.getenv("KITE_API_SECRET", "")

import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "portfolio.db"

# Note: The global environment values used in this file are attached in appendix in each student's individual report.

STARTING_CAPITAL = 
MIN_TICKERS = 
MAX_TICKERS = 
MAX_ASSET_WEIGHT = 

HISTORY_DAYS = 
MARKET_BENCHMARK = 
BAR_TIMEFRAME = 

RISK_FREE_RATE = 
VAR_CONFIDENCE = 
TRADING_DAYS = 
ROUND_DECIMALS = 

MOMENTUM_LOOKBACK_SHORT = 
MOMENTUM_LOOKBACK_MEDIUM = 
MOMENTUM_LOOKBACK_LONG = 
TOP_N_SELECTION = 

DEFAULT_STRATEGY_MODE = 
DEFAULT_WEIGHTING_METHOD = 

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_DATA_FEED = "iex"

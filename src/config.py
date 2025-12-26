import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Exchange Configuration
    API_KEY = os.getenv("BINANCE_API_KEY")
    SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
    IS_TESTNET = os.getenv("IS_TESTNET", "True").lower() == "true"
    
    # Trading Parameters
    INITIAL_EQUITY = 200.0  # USDT
    TARGET_COIN_COUNT = 20
    TARGET_VALUE_PER_COIN = 20.0  # USDT
    LEVERAGE = 5
    EFFECTIVE_LEVERAGE = 2.0
    
    # Rebalancing Parameters
    REBALANCE_THRESHOLD_PCT = 0.05  # 5%
    SCAN_INTERVAL_MINUTES = 5
    
    # Risk Management
    MAX_DRAWDOWN_PCT = 0.30  # 30%
    MAX_FUNDING_RATE_APR = 1.00 # 100% APR
    
    # Minimum Order Value (Binance Futures constraint)
    # Typically 5 USDT, keeping it slightly higher to be safe
    MIN_ORDER_VALUE = 5.1 

    # Dynamic Whitelist (to be populated by Scanner)
    # Initial manual list for testing if scanner not ready
    DEFAULT_COINS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT",
        "XRP/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT"
    ]

    @classmethod
    def validate(cls):
        if not cls.API_KEY or not cls.SECRET_KEY:
            raise ValueError("API credentials missing. Please set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")

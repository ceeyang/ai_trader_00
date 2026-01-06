import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Exchange Configuration
    # Using alias to map env vars to fields
    API_KEY: str = Field(..., alias="BINANCE_API_KEY")
    SECRET_KEY: str = Field(..., alias="BINANCE_SECRET_KEY")
    IS_TESTNET: bool = Field(default=True)
    
    # Trading Parameters
    INITIAL_EQUITY: float = 200.0  # USDT
    TARGET_COIN_COUNT: int = 20
    TARGET_VALUE_PER_COIN: float = 20.0  # USDT
    
    # Rebalancing Parameters
    REBALANCE_THRESHOLD_PCT: float = 0.05  # 5%
    SCAN_INTERVAL_MINUTES: int = 5
    
    # Risk Management
    MAX_DRAWDOWN_PCT: float = 0.30  # 30%
    MAX_FUNDING_RATE_APR: float = 1.00 # 100% APR
    
    # Minimum Order Value (Binance Futures constraint)
    MIN_ORDER_VALUE: float = 5.1 

    # Dynamic Whitelist (fallback)
    DEFAULT_COINS: List[str] = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT",
        "XRP/USDT", "ADA/USDT", "AVAX/USDT", "LINK/USDT", "DOT/USDT"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore" 

# Global instance
try:
    Config = Settings()
    # Backward compatibility for class-based usage if needed, 
    # but simplest is to just use 'Config' instance directly as before.
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    # Fallback/Exit? For now raise so user sees it
    raise e

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
    API_KEY: Optional[str] = Field(None, alias="BINANCE_API_KEY")
    SECRET_KEY: Optional[str] = Field(None, alias="BINANCE_SECRET_KEY")
    
    # Testnet Specific Keys
    TESTNET_API_KEY: Optional[str] = Field(None, alias="BINANCE_TESTNET_API_KEY")
    TESTNET_SECRET_KEY: Optional[str] = Field(None, alias="BINANCE_TESTNET_SECRET_KEY")
    
    IS_TESTNET: bool = Field(default=True)
    
    # Trading Parameters
    INITIAL_EQUITY: float = 200.0  # USDT (Reference only, logic uses actual)
    
    # Strategy
    MAX_OPEN_POSITIONS: int = 10 # Maximum number of coins to hold
    LEVERAGE: int = 5
    EFFECTIVE_LEVERAGE: float = 2.0 # Target total exposure multiplier (e.g. 2.0x of Equity)
    
    # Weights configuration (Symbol -> Weight 0.0 to 1.0)
    # Remaining weight is distributed equally among other selected coins
    COIN_WEIGHTS: Dict[str, float] = {
        "BTC/USDT": 0.4, # 40% allocation to BTC
        "ETH/USDT": 0.3, # 30% allocation to ETH
    }
    
    # Rebalancing Parameters
    REBALANCE_THRESHOLD_PCT: float = 0.05  # 5% deviation triggers trade
    SCAN_INTERVAL_MINUTES: int = 5
    
    # Risk Management
    MAX_DRAWDOWN_PCT: float = 0.30  # Global Account Stop Loss
    MAX_POS_DRAWDOWN_PCT: float = 0.15 # Single Position Stop Loss (15%)
    MAX_FUNDING_RATE_APR: float = 1.00 # 100% APR
    MAX_MARGIN_UTILIZATION_PCT: float = 0.80 # Max 80% of Equity used as Margin
    
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

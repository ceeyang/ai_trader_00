import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.exchange import BinanceClient
from src.market_scanner import MarketScanner
from src.config import Config

def main():
    print("🔍 Initializing Scanner...")
    
    if Config.IS_TESTNET:
        print("\n" + "="*50)
        print("⚠️  WARNING: RUNNING IN TESTNET MODE")
        print("   - You will see test assets (e.g., MILK, 0G)")
        print("   - These are NOT real Mainnet coins")
        print("   - Set IS_TESTNET=False in .env for Real Trading")
        print("="*50 + "\n")

    try:
        client = BinanceClient()
        if not client.validate_connectivity():
            return
            
        scanner = MarketScanner(client)
        print("📊 executing market scan...")
        top_coins = scanner.get_top_coins(limit=50)
        
        print("\n✅ Recommended Assets to Buy (Top Selected):")
        print("---------------------------------------------")
        for i, coin in enumerate(top_coins, 1):
            print(f"{i}. {coin}")
        print("---------------------------------------------")
        print(f"Total: {len(top_coins)} coins selected.")
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")

if __name__ == "__main__":
    main()

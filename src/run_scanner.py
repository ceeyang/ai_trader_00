import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.exchange import BinanceClient
from src.market_scanner import MarketScanner

def main():
    print("🔍 Initializing Scanner...")
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

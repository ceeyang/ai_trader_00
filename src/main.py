import time
import schedule
from config import Config
from exchange import BinanceClient
from market_scanner import MarketScanner
from risk_manager import RiskManager
from rebalancer import Rebalancer
from reporter import Reporter

def main():
    print("=== 🚀 Starting Quantitative Trading Bot (Index-style Long) ===")
    
    # 1. Initialize Components
    try:
        client = BinanceClient()
        if not client.validate_connectivity():
            return
            
        scanner = MarketScanner(client)
        risk_manager = RiskManager()
        rebalancer = Rebalancer(client, risk_manager)
        # reporter = Reporter() # Optional usage in Rebalancer if we injected it
    
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Define Job Wrapper
    def job():
        try:
            # Step A: Scan for Target Coins (or use default)
            # In a real run, you might cache this or run it less frequently (e.g. hourly)
            # For now, we run it every cycle or use a cached list logic.
            # To avoid API spam, let's keep using the scanner, but maybe we only update the list every 4 hours?
            # For simplicity in this structure: Get coins.
            
            # coins = scanner.get_top_coins() 
            # OR for stability/testing:
            coins = Config.DEFAULT_COINS
            if not coins:
                print("⚠️ No coins to trade.")
                return

            # Step B: Rebalance
            rebalancer.rebalance(coins)
            
        except Exception as e:
            print(f"❌ Job Failed: {e}")

    # 3. Schedule Jobs
    schedule.every(Config.SCAN_INTERVAL_MINUTES).minutes.do(job)
    
    print(f"✅ Bot Scheduled: Running every {Config.SCAN_INTERVAL_MINUTES} minutes...")
    
    # Run once immediately on startup
    job()
    
    # 4. Loop
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
